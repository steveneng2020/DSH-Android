#!/usr/bin/env node
// 推理档位自动适配：三层自动查表 + 安全回写（用户 2026-10-25 拍板方案 B）。
//
// 为什么需要它（根因，file:line）：
//   dsh-llm-pi-ai/lib/index.js:585-587
//     const efforts = entry.reasoningEfforts;
//     if (efforts === void 0) return { reasoning: base?.reasoning ?? false };
//   base 来自 pi-ai 内置目录（同文件 :688 defaults.get(entry.id)）。官方模型命中目录 →
//   reasoning:true → UI 出现「推理等级」行；第三方模型不在目录里 → base undefined →
//   reasoning:false → 整行消失。所以**开关在配置**：给模型补 reasoningEfforts 即可，
//   不需要（也禁止）改宿主 npm 包。
//
// 三层策略（越靠前越可信，命中即停）：
//   L1  pi-ai 内置目录：按 model id 在 MODELS 全部 catalog provider 里找，只在**档位集合唯一**
//       时命中；多个 provider 给出不同集合 ⇒ 多义，交给 L2（不能只按 id 猜）。
//   L2  provider 规则表：不写死，从**同一个 profile** 里该 provider 已有 reasoningEfforts 的
//       模型归纳众数（用户 72 处配置就是这张表的来源）。并列众数 ⇒ 不确定，交给 L3。
//   L3  动态探测：用该 provider 的 apiKeyEnv 凭据，依次发 reasoning_effort=<level>；
//       只探测前两层仍不确定的模型；失败/限流/超时一律跳过，不写配置。
//
// 写入安全（用户硬要求）：
//   · 只增不改：已有 reasoningEfforts 的模型直接跳过，不覆盖手调值
//   · 0 档保护：确认没有任何思考档 ⇒ **不写**字段（绝不写 {} 或 null，
//     dsh-llm-pi-ai/lib/index.js:589 会抛错并带走整个 provider）
//   · off 一律写 null（=不发送 reasoning 字段），不写字符串 "null"/none
//   · 备份 → 同目录临时文件 → fsync → rename → 重新解析校验 → 失败回滚
//
// 用法：
//   node reasoning-autofit.cjs <含 yaml 与 @earendil-works/pi-ai 的 node_modules>
//        --profile <cordis.patch.yml> [--credentials <.credentials.yaml>]
//        [--dry-run] [--no-probe] [--progress <file>] [--timeout-ms 15000]
// 输出最后一行：DSHA_REASONING_AUTOFIT=<json>

'use strict'

const fs = require('node:fs')
const path = require('node:path')

/** pi-ai 的升序档位（dsh-llm-pi-ai/lib/index.js:298-307 与 pi-ai dist/models.js:679 逐字一致）。 */
const LEVELS = ['off', 'minimal', 'low', 'medium', 'high', 'xhigh', 'max']

/** 探测顺序：从低到高。off 不探测（=不发送字段，永远可用）。 */
const PROBE_LEVELS = ['low', 'medium', 'high', 'xhigh', 'max']

/** 一次运行最多探测多少个模型（成本护栏）。 */
const MAX_PROBE_MODELS = 12

/**
 * 已知 0 档模型：**无论三层算出什么，一律不写**。
 *
 * 出处（两条独立证据）：
 *   1) 用户现行 profile 里这两个模型**没有** reasoningEfforts（只读解析，74 条里唯一 2 条未声明）；
 *   2) captain 2026-10-25 实测结论：「doubao / doubao-pro 不声明 reasoningEfforts（0 档）」。
 *
 * 为什么必须单独拦：`doubao` 这个 provider 下另外 2 个模型都是 6 档，L2 的众数规则会
 * 把 6 档"外推"给这两个模型 —— 但用户明确要求它们保持 0 档。给它们写档位的后果不是
 * "多一个选项"，而是 `dsh-llm-pi-ai` 按档位发 `reasoning_effort`，上游不认就整次请求失败。
 */
const ZERO_TIER_GUARD = [
  { provider: 'doubao', model: 'doubao' },
  { provider: 'doubao', model: 'doubao-pro' },
]

/** 该 (provider, model) 是否在 0 档保护名单里。 */
function isZeroTierGuard(providerId, modelId) {
  return ZERO_TIER_GUARD.some(row => row.provider === providerId && row.model === modelId)
}

/**
 * 第二层的**内置**规则表：captain 2026-10-25 从用户现行 profile 的 72 处配置归纳的实测规律。
 *
 * 与 `providerRule()`（从 profile 现读的众数）互补：
 *   · profile 里该 provider 还有已声明模型 → 用**现读众数**（用户改过配置就跟着变，优先）
 *   · profile 里该 provider 一个都没声明（如用户清空过） → 用这张表兜底
 *   · 两者都有但不一致 → 不下结论，交给第三层探测
 *
 * ⚠ 这张表只描述「这个 provider 普遍怎么配」，不是「上游一定支持什么」：`doubao` 的
 * `doubao` / `doubao-pro` 就是同 provider 里的 0 档例外，由 {@link ZERO_TIER_GUARD} 拦。
 */
const PROVIDER_RULES = {
  trae: {levels: LEVELS.slice()},
  dshapipojia: {levels: ['off', 'low', 'high', 'max']},
  workbuddyold: {levels: LEVELS.slice(), exceptions: {'mimo-v2.6-pro': ['off', 'low', 'high', 'max']}},
  xongzhou2: {levels: LEVELS.slice()},
  xingzhou3: {levels: LEVELS.slice()},
  doubao: {levels: LEVELS.slice()},
}

/** 内置规则表命中的档位（含 per-model 例外）；无规则返回 null。 */
function builtinRule(providerId, modelId) {
  const rule = PROVIDER_RULES[providerId]
  if (!rule) return null
  const levels = (rule.exceptions && rule.exceptions[modelId]) || rule.levels
  return {levels: levels.slice(), source: 'builtin-rule'}
}

/** 单次探测请求超时。 */
const DEFAULT_TIMEOUT_MS = 15000

/**
 * 与宿主 getSupportedThinkingLevels（pi-ai dist/models.js:680-690）同款的集合推导。
 * @param {object} entry - catalog 模型条目（reasoning / thinkingLevelMap）。
 * @returns {string[]} 升序档位；不思考的模型返回空数组。
 */
function supportedLevels(entry) {
  if (!entry || entry.reasoning !== true) return []
  const map = entry.thinkingLevelMap || {}
  return LEVELS.filter(level => {
    const mapped = map[level]
    if (mapped === null) return false
    if (level === 'xhigh' || level === 'max') return mapped !== undefined
    return true
  })
}

/** 档位集合签名（按 LEVELS 升序，集合本身无序）。 */
function signature(levels) {
  return [...new Set(levels)].sort((a, b) => LEVELS.indexOf(a) - LEVELS.indexOf(b)).join(',')
}

/**
 * L1：pi-ai 内置目录查表，只在集合唯一时命中。
 * @param {Record<string, Record<string, object>>} models - models.generated 的 MODELS。
 * @param {string} modelId
 * @returns {{levels: string[], providers: string[]}|null}
 */
function lookupCatalog(models, modelId) {
  if (!models || typeof modelId !== 'string' || !modelId) return null
  const hits = []
  for (const provider of Object.keys(models)) {
    const entry = models[provider] && models[provider][modelId]
    if (!entry) continue
    const levels = supportedLevels(entry)
    if (levels.length === 0) continue
    hits.push({ provider, levels })
  }
  if (hits.length === 0) return null
  if (new Set(hits.map(hit => signature(hit.levels))).size !== 1) return null
  return { levels: hits[0].levels, providers: hits.map(hit => hit.provider) }
}

/**
 * L2：从同一 profile 的**已有配置**归纳该 provider 的众数档位集合。
 * 只有唯一最高票才算规则；并列最高票即不确定（返回 null）。
 * @param {Array<{reasoningEfforts?: object}>} models
 * @returns {{levels: string[], votes: number, total: number}|null}
 */
function providerRule(models) {
  const tally = new Map()
  let total = 0
  for (const model of models || []) {
    const efforts = model && model.reasoningEfforts
    if (!efforts || typeof efforts !== 'object') continue
    const levels = Object.keys(efforts).filter(level => LEVELS.includes(level))
    if (levels.length === 0) continue
    total += 1
    const key = signature(levels)
    tally.set(key, (tally.get(key) || 0) + 1)
  }
  if (total === 0) return null
  const ranked = [...tally.entries()].sort((a, b) => b[1] - a[1])
  if (ranked.length > 1 && ranked[1][1] === ranked[0][1]) return null
  return { levels: ranked[0][0].split(','), votes: ranked[0][1], total }
}

/**
 * 档位集合 → profile 里要写的 reasoningEfforts 映射。
 * `off` 一律 null；其余档位按同名 wire 值；只有 off 等于 0 档 → 返回 null（不写）。
 * @param {string[]} levels
 * @returns {Record<string, string|null>|null}
 */
function toEfforts(levels) {
  const set = new Set((levels || []).filter(level => LEVELS.includes(level)))
  if (set.size === 0) return null
  const efforts = {}
  for (const level of LEVELS) {
    if (!set.has(level)) continue
    efforts[level] = level === 'off' ? null : level
  }
  if (Object.keys(efforts).every(level => level === 'off')) return null
  return efforts
}

/** 从 .credentials.yaml 的 refs 取字面量键值（只读；不打印、不落盘）。 */
function readCredentials(text, envName) {
  if (typeof text !== 'string' || typeof envName !== 'string' || !envName) return null
  const escaped = envName.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
  const match = new RegExp('^\\s+' + escaped + ':\\s*(\\S.*)$', 'm').exec(text)
  if (!match) return null
  const value = match[1].trim().replace(/^['"]|['"]$/g, '')
  return value || null
}

/** 发一个探测请求，判定该档位是否被上游接受。 */
async function probeLevel({ baseURL, apiKey, model, level, timeoutMs }) {
  const url = String(baseURL).replace(/\/+$/, '') + '/chat/completions'
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeoutMs)
  try {
    const response = await fetch(url, {
      method: 'POST',
      headers: { 'content-type': 'application/json', authorization: 'Bearer ' + apiKey },
      body: JSON.stringify({
        model,
        messages: [{ role: 'user', content: 'ping' }],
        max_tokens: 1,
        stream: false,
        reasoning_effort: level,
      }),
      signal: controller.signal,
    })
    if (response.ok) return 'supported'
    const body = await response.text().catch(() => '')
    if (response.status === 400 || response.status === 422) {
      // 只有明确指向 reasoning/effort 的 4xx 才算「不支持」；其它 4xx 视为不可下结论。
      return /reasoning|effort|thinking/i.test(body) ? 'unsupported' : 'inconclusive'
    }
    if (response.status === 429 || response.status >= 500) return 'transient'
    return 'inconclusive'
  } catch {
    return 'transient'
  } finally {
    clearTimeout(timer)
  }
}

/** 依次探测一个模型的全部档位；任一档位探测不可信 ⇒ 整个模型返回 null。 */
async function probeModel(options) {
  const supported = ['off']
  for (const level of PROBE_LEVELS) {
    const verdict = await probeLevel({ ...options, level })
    if (verdict === 'supported') supported.push(level)
    else if (verdict !== 'unsupported') return null
  }
  return supported
}

/**
 * 规划：对每个「没有 reasoningEfforts」的模型给出决策（不写盘、不联网）。
 * @returns {{plan: Array<object>, needsProbe: Array<object>}}
 */
function planModels({ providers, catalog, probeEnabled }) {
  const plan = []
  const needsProbe = []
  for (const [providerId, provider] of Object.entries(providers || {})) {
    const models = Array.isArray(provider && provider.models) ? provider.models : []
    const rule = providerRule(models)
    for (const model of models) {
      if (!model || typeof model.id !== 'string') continue
      if (model.reasoningEfforts !== undefined) {
        plan.push({ provider: providerId, model: model.id, action: 'skip', reason: 'already-declared' })
        continue
      }
      // 0 档保护优先于三层：用户明确要它们保持"不发送 reasoning"。
      if (isZeroTierGuard(providerId, model.id)) {
        plan.push({ provider: providerId, model: model.id, action: 'skip', reason: 'zero-tier-guard' })
        continue
      }
      const hit = lookupCatalog(catalog, model.id)
      const builtin = builtinRule(providerId, model.id)
      // 证据优先级（同 provider 的实测 > 跨 provider 的同名条目）：
      //   ① profile 里同 provider 已有声明的众数（provider-rule）—— 用户自己配过，最可信
      //   ② 内置 provider 规则表（captain 从同一份 profile 72 处配置归纳）
      //   ③ pi-ai 内置目录：**只按 model id** 匹配，条目属于别家端点，与①②冲突时让位
      //   ④ 三层都空 → 交给探测
      // 曾按"catalog 优先"实现过，实测会出错：catalog 的 hy3 是 3 档（off/low/high），
      // 而用户 workbuddyold 的 hy3 明确声明 6 档；照 catalog 写会把 medium/xhigh 从用户
      // 手里删掉。故改为同 provider 证据优先，并在 decisions 里记下分歧供人工复核。
      const same = rule !== null
        ? {levels: rule.levels, source: 'provider-rule', votes: rule.votes, total: rule.total}
        : builtin
      const catalogEvidence = hit !== null ? {levels: hit.levels, source: 'catalog'} : null
      const conflict = hit !== null && same !== null && signature(hit.levels) !== signature(same.levels)
      const evidence = same !== null ? same : catalogEvidence
      if (evidence !== null) {
        const efforts = toEfforts(evidence.levels)
        plan.push({
          provider: providerId, model: model.id, action: efforts ? 'write' : 'skip',
          source: evidence.source, levels: evidence.levels, efforts,
          ...rule !== null && same.source === 'provider-rule' ? {votes: rule.votes, total: rule.total} : {},
          ...conflict ? {catalogLevels: hit.levels} : {},
        })
        continue
      }
      if (probeEnabled) {
        const pending = { provider: providerId, model: model.id, action: 'probe', source: 'probe' }
        plan.push(pending)
        needsProbe.push(pending)
      } else {
        plan.push({ provider: providerId, model: model.id, action: 'skip', reason: 'uncertain' })
      }
    }
  }
  return { plan, needsProbe }
}

/** 取 scalar 节点的字面值。 */
function valueOf(node) {
  return node && typeof node === 'object' && 'value' in node ? node.value : undefined
}

/**
 * 读取并解析 profile；任何实质告警都当失败（宁可不动用户的配置）。
 *
 * 2026-11-10 修：cordis.patch.yml 用 `!!js` 承载运行时才求值的 JavaScript 表达式
 * （如 `disabled: !!js process.platform === 'win32'`）。yaml 库不认识该标签，
 * 会对每一处产生 "Unresolved tag: tag:yaml.org,2002:js" 告警——实测真机 profile
 * 有 13 条，全部是这个原因。原先「任何 warning 都失败」使自动适配在该 profile 上
 * 100% 抛 PROFILE_YAML_INVALID，从未成功过一次。
 *
 * `!!js` 是 cordis 的合法语法，不是配置错误，故豁免这一类告警；
 * 其余告警仍按原策略失败。豁免不影响写回：实测原文 14 处 !!js 全部逐字保留，
 * 整份文档写回后字节一致。
 */
function parseProfile(yaml, text) {
  const doc = yaml.parseDocument(text, { uniqueKeys: true })
  const blocking = doc.warnings.filter(
    warning => !/^Unresolved tag: tag:yaml\.org,2002:js\b/.test(String(warning && warning.message)))
  if (doc.errors.length || blocking.length) throw new Error('PROFILE_YAML_INVALID')
  const items = doc.contents && Array.isArray(doc.contents.items) ? doc.contents.items : []
  const entry = items.find(item => item && typeof item.get === 'function' && valueOf(item.get('id', true)) === 'llm-pi-ai')
  if (!entry) throw new Error('PROFILE_LLM_ENTRY_MISSING')
  const config = entry.get('config', true)
  const providers = config && typeof config.get === 'function' ? config.get('providers', true) : undefined
  if (!providers || !Array.isArray(providers.items)) throw new Error('PROFILE_PROVIDERS_MISSING')
  return { doc, entry, providers }
}

/**
 * providers 的只读普通对象视图（供规划用；模型条目只取 id 与 reasoningEfforts 键集合）。
 * @param {object} yaml
 * @param {object} providers - providers 的 YAMLMap 节点。
 */
function providersToJS(yaml, providers) {
  const result = {}
  for (const pair of providers.items || []) {
    const key = valueOf(pair.key)
    if (typeof key !== 'string' || !yaml.isMap(pair.value)) continue
    const modelsNode = pair.value.get('models', true)
    const models = yaml.isSeq(modelsNode)
      ? modelsNode.items.map(item => {
        if (!yaml.isMap(item)) return {}
        const out = { id: valueOf(item.get('id', true)) }
        const efforts = item.get('reasoningEfforts', true)
        if (yaml.isMap(efforts)) {
          const map = {}
          for (const effortPair of efforts.items || []) {
            const level = valueOf(effortPair.key)
            if (typeof level === 'string') map[level] = valueOf(effortPair.value) ?? null
          }
          out.reasoningEfforts = map
        }
        return out
      })
      : []
    result[key] = { models, node: pair.value }
  }
  return result
}

/**
 * 把决定写回 AST：只在模型条目里**追加** reasoningEfforts（保留原有注释与顺序）。
 * @returns {number} 实际写入的模型数。
 */
function applyEfforts(yaml, providers, plan) {
  let changed = 0
  for (const item of plan) {
    if (item.action !== 'write' || !item.efforts) continue
    const provider = providers[item.provider]
    if (!provider || !yaml.isMap(provider.node)) continue
    const modelsNode = provider.node.get('models', true)
    if (!yaml.isSeq(modelsNode)) continue
    for (const modelNode of modelsNode.items) {
      if (!yaml.isMap(modelNode)) continue
      if (valueOf(modelNode.get('id', true)) !== item.model) continue
      if (modelNode.get('reasoningEfforts', true) !== undefined) continue // 只增不改
      modelNode.set('reasoningEfforts', item.efforts)
      changed += 1
      break
    }
  }
  return changed
}

/** 原子写：同目录临时文件 → fsync → rename。 */
function atomicWrite(file, text) {
  const temp = path.join(path.dirname(file), '.' + path.basename(file) + '.autofit-' + process.pid)
  const handle = fs.openSync(temp, 'w', 0o600)
  try {
    fs.writeFileSync(handle, text, 'utf8')
    fs.fsyncSync(handle)
  } finally {
    fs.closeSync(handle)
  }
  fs.renameSync(temp, file)
}

/** 备份到 <profile>.bak-before-autoeffort-<timestamp>（同目录、0600）。 */
function backup(file, stamp) {
  const target = file + '.bak-before-autoeffort-' + stamp
  fs.copyFileSync(file, target)
  fs.chmodSync(target, 0o600)
  return target
}

const nowStamp = () => new Date().toISOString().replace(/[-:T]/g, '').replace(/\..*$/, '')

/**
 * 主流程：读 profile → 规划 →（可选）探测 → 写回。
 * @param {object} options
 * @returns {Promise<object>} 汇总（可直接 JSON 化）。
 */
async function run(options) {
  const { yaml, profilePath, catalog, credentialsText, apply, probe, progress, timeoutMs } = options
  const text = fs.readFileSync(profilePath, 'utf8')
  const { doc, providers } = parseProfile(yaml, text)
  const view = providersToJS(yaml, providers)
  const { plan, needsProbe } = planModels({ providers: view, catalog, probeEnabled: probe !== false })
  const summary = {
    profile: profilePath, total: plan.length, written: 0, skipped: 0,
    probed: 0, probeSkipped: 0, changed: false, breakdown: {},
  }
  const report = value => {
    if (typeof progress === 'function') progress(value)
    summary.breakdown[value.action] = (summary.breakdown[value.action] || 0) + 1
  }
  for (const item of plan) report(item)

  if (apply !== false && needsProbe.length > 0) {
    const limited = needsProbe.slice(0, MAX_PROBE_MODELS)
    summary.probeSkipped = needsProbe.length - limited.length
    if (typeof progress === 'function') progress({ phase: 'probe', done: 0, total: limited.length })
    for (let index = 0; index < limited.length; index += 1) {
      const item = limited[index]
      const node = view[item.provider] && view[item.provider].node
      const baseURL = node && typeof node.get === 'function' ? valueOf(node.get('baseURL', true)) : undefined
      const envName = node && typeof node.get === 'function' ? valueOf(node.get('apiKeyEnv', true)) : undefined
      const apiKey = readCredentials(credentialsText, envName)
      if (typeof progress === 'function') progress({ phase: 'probe', done: index, total: limited.length, provider: item.provider, model: item.model })
      if (!baseURL || !apiKey) { item.action = 'skip'; item.reason = 'missing-credential'; continue }
      const levels = await probeModel({ baseURL, apiKey, model: item.model, timeoutMs: timeoutMs || DEFAULT_TIMEOUT_MS })
      summary.probed += 1
      if (levels === null) { item.action = 'skip'; item.reason = 'probe-inconclusive'; continue }
      const efforts = toEfforts(levels)
      if (!efforts) { item.action = 'skip'; item.reason = 'no-reasoning-support'; continue }
      Object.assign(item, { action: 'write', levels, efforts })
    }
    if (typeof progress === 'function') progress({ phase: 'probe', done: limited.length, total: limited.length })
  }

  const changed = apply !== false ? applyEfforts(yaml, view, plan) : 0
  summary.written = changed
  summary.skipped = plan.filter(item => item.action !== 'write').length
  if (changed > 0) {
    const output = doc.toString({ lineWidth: 0 })
    parseProfile(yaml, output) // 写前自检：能解析才落盘
    const saved = backup(profilePath, nowStamp())
    try {
      atomicWrite(profilePath, output)
      parseProfile(yaml, fs.readFileSync(profilePath, 'utf8')) // 写后复检
      summary.changed = true
      summary.backup = saved
    } catch (error) {
      fs.copyFileSync(saved, profilePath)
      throw new Error('PROFILE_WRITE_ROLLED_BACK: ' + (error && error.message ? error.message : String(error)))
    }
  }
  summary.decisions = plan.filter(item => item.action !== 'skip' || item.reason !== 'already-declared')
  return summary
}

module.exports = {
  LEVELS, PROBE_LEVELS, MAX_PROBE_MODELS, DEFAULT_TIMEOUT_MS, ZERO_TIER_GUARD, isZeroTierGuard,
  PROVIDER_RULES, builtinRule,
  supportedLevels, signature, lookupCatalog, providerRule, toEfforts, readCredentials,
  probeLevel, probeModel, planModels, parseProfile, providersToJS, applyEfforts, atomicWrite, run,
}

if (require.main === module) {
  (async () => {
    const args = process.argv.slice(2)
    const moduleDir = args[0]
    const flag = name => {
      const at = args.indexOf('--' + name)
      return at >= 0 ? args[at + 1] : undefined
    }
    const has = name => args.includes('--' + name)
    const emit = value => process.stdout.write('DSHA_REASONING_AUTOFIT=' + JSON.stringify(value) + '\n')
    try {
      const yaml = require(path.join(moduleDir, 'yaml'))
      const catalog = require(path.join(moduleDir, '@earendil-works/pi-ai/dist/models.generated.js')).MODELS
      const home = process.env.DSH_HOME || '/root/.dsh'
      const profilePath = flag('profile') || path.join(home, 'profiles/web/cordis.patch.yml')
      const credentialsPath = flag('credentials') || path.join(home, '.credentials.yaml')
      const progressPath = flag('progress')
      const progress = progressPath
        ? value => { try { fs.writeFileSync(progressPath, JSON.stringify(value) + '\n') } catch {} }
        : undefined
      const credentialsText = fs.existsSync(credentialsPath) ? fs.readFileSync(credentialsPath, 'utf8') : ''
      emit(await run({
        yaml, profilePath, catalog, credentialsText,
        apply: !has('dry-run'),
        probe: !has('no-probe'),
        progress,
        timeoutMs: Number(flag('timeout-ms')) || DEFAULT_TIMEOUT_MS,
      }))
    } catch (error) {
      emit({ ok: false, error: String(error && error.message ? error.message : error) })
      process.exitCode = 3
    }
  })()
}
