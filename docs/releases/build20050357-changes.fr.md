# DSHA v1.4 20261111@0.2.2-rc.1 / build20050357

Cette build est reconstruite sur la base DSHA upstream 0.2.2 (build357) et embarque DSH 0.2.2-rc.1 ; l'environnement de base Ubuntu reste 10.

- Mise à niveau de la base : d'upstream 0.2.1-rc.2 (build190) vers 0.2.2 (build357), avec l'interface mobile v5, une page autonome d'autorisation des capacités de l'appareil et le correctif de blocage d'enregistrement des plugins pendant la maintenance.
- Variante unique : la ligne de compatibilité et GeckoView sont supprimés ; seule Standard est distribuée (Android 11+, arm64-v8a, WebView système).
- Fonctions propres au fork conservées : icône cliquable avec six jeux de couleurs, panneau du journal des mises à jour, comparaison avec upstream, ajustement automatique du niveau de raisonnement, vérification des dépendances natives des plugins.
- Identité de publication indépendante : paquet `dsh.android.dev` et certificat propre, non interchangeables avec upstream `dsh.android.client` ; l'installation par-dessus exige la même signature.
- La source de mise à jour reste `updates.json` de ce dépôt ; les APK sont servis par les Releases de ce dépôt.

Le `versionCode` de cette build est `20050357`. Les utilisateurs d'une version antérieure ne la verront pas dans « rechercher des mises à jour » (un versionCode supérieur est requis) et doivent l'installer manuellement.
Les vérifications logicielles et la recette sur appareil se limitent au reçu de cette campagne et ne prouvent pas une matrice complète d'appareils.
