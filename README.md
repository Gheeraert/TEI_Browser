# TEI Reader

Lecteur TEI-XML autonome en Python. Chaîne de traitement :

```
TEI-XML → lxml (parsing sécurisé + diagnostics) → SaxonC-HE (XSLT 3.0) → HTML statique → webview / navigateur
```

Ce projet est l'**étape 0** d'un lecteur savant de textes TEI (littérature française,
édition critique), lui-même étape intermédiaire vers une future extension Firefox.
Voir [docs/architecture.md](docs/architecture.md) pour la vision d'ensemble et
[docs/contrat-html.md](docs/contrat-html.md) pour le contrat de rendu HTML,
qui est le capital central du projet.

## Principes

- Technologies libres uniquement (SaxonC-HE est sous MPL-2.0 ; Saxon-JS,
  gratuit mais non libre, est exclu de l'architecture).
- Pas de base de données, pas de réseau, HTML statique reproductible.
- Séparation stricte : cœur métier / moteur de transformation / profils /
  interface. Aucune interface ne touche Saxon directement.
- Le lecteur ne plante jamais sur un TEI imprévu : les éléments inconnus
  sont rendus lisiblement (fallback `data-tei`) et signalés en diagnostic.

## Installation

Prérequis : Windows, Python 3.11–3.13 (3.13 recommandé ; testé avec 3.13).

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\pip install -e ".[ui,dev]"
```

Les extras : `ui` installe pywebview (affichage via Edge WebView2, déjà présent
sous Windows 11) ; `dev` installe pytest.

## Utilisation

```powershell
# Transformer un fichier TEI en HTML (dossier ./out par défaut)
.\.venv\Scripts\tei-reader render samples\prose.xml --profile prose
.\.venv\Scripts\tei-reader render samples\verse.xml --profile verse
.\.venv\Scripts\tei-reader render samples\drama.xml --profile drama
.\.venv\Scripts\tei-reader render samples\apparatus.xml --profile diagnostic
.\.venv\Scripts\tei-reader render samples\correspondence.xml --profile correspondence
.\.venv\Scripts\tei-reader render samples\images.xml --profile prose

# Transformer et ouvrir dans le navigateur par défaut
.\.venv\Scripts\tei-reader render samples\prose.xml --open

# Transformer et afficher dans une fenêtre webview
.\.venv\Scripts\tei-reader view samples\drama.xml --profile drama

# Ouvrir l'interface desktop de consultation
.\.venv\Scripts\tei-reader gui
.\.venv\Scripts\python -m tei_reader gui

# Analyser un fichier sans produire de HTML (résumé + diagnostics)
.\.venv\Scripts\tei-reader inspect samples\drama.xml

# Lister les profils disponibles
.\.venv\Scripts\tei-reader profiles
```

(`python -m tei_reader …` fonctionne à l'identique.)

Chaque rendu produit dans le dossier de sortie :

- `<nom>.html` — le document transformé (autonome, CSS copiées à côté) ;
- `<nom>.diagnostics.json` — les avertissements (éléments non traités, etc.).

## Profils

Cinq profils, définis dans `tei_reader/resources/profiles/` :

- **prose** — lecture courante (roman, essai, correspondance) : notes en
  fin de document, apparat réduit à la leçon retenue ;
- **verse** — poésie : strophes, numéros de vers dans la marge, vers
  partagés (`@part`) en retrait ;
- **drama** — théâtre : actes/scènes centrés, locuteurs en petites
  capitales, didascalies distinctes, distribution encadrée ;
- **correspondence** — lettres : date et lieu à droite, salutation
  détachée, signature, adresse encadrée ;
- **diagnostic** — éléments non traités surlignés avec leur nom TEI,
  apparat complet (leçons, variantes, témoins), notes inline.

Un profil est un JSON : feuille XSLT d'entrée, paramètres de transformation
(dont `note-mode` : `inline` ou `end`), liste de CSS. Modifier un profil ou
une CSS ne demande jamais de toucher au XSLT.

## Structure du projet

```
tei_reader/
├── cli.py                  # interface ligne de commande
├── core/
│   ├── document.py         # parsing lxml sécurisé, inventaire des éléments
│   └── service.py          # façade unique : render()
├── transform/
│   ├── engine.py           # interface abstraite TransformEngine
│   └── saxon_engine.py     # implémentation saxonche (seul import de saxonche)
├── diagnostics/models.py   # Diagnostic, RenderResult
├── profiles/loader.py      # chargement des profils JSON
├── ui/
│   ├── app.py              # interface desktop pywebview
│   ├── webview_app.py      # affichage simple d'un HTML rendu
│   └── assets/             # HTML/CSS/JS de l'interface desktop
└── resources/
    ├── xsl/tei-common.xsl  # transformation TEI → HTML5 (contrat HTML)
    ├── css/                # base, verse, drama, correspondence, apparatus, diagnostic
    └── profiles/           # prose, verse, drama, correspondence, diagnostic (JSON)
samples/                    # échantillons ciblés (un par fonctionnalité + stress-mixed)
fixtures/                   # TEI réels et variés pour audit empirique
tests/                      # pytest (dont snapshots/ : HTML de non-régression)
docs/                       # architecture, contrat HTML, audit des fallbacks
```

## Tests

```powershell
.\.venv\Scripts\python -m pytest
```

Les tests garantissent au minimum : un TEI simple produit du HTML conforme au
contrat ; un élément inconnu ne fait pas planter la transformation ; les
diagnostics sont produits ; un XML mal formé échoue proprement (pas d'exception,
un `RenderResult` d'erreur) ; le fichier de stress (tous genres mêlés,
références cassées, image absente) se rend sans crash sous les cinq profils.

**Snapshots de non-régression** : le HTML produit est comparé à des
snapshots normalisés (`tests/snapshots/`). Si un test de snapshot échoue
après un changement *voulu* du rendu, régénérer volontairement puis
relire le diff git :

```powershell
.\.venv\Scripts\python tests\update_snapshots.py
```

## Lancer depuis PyCharm

1. Ouvrir le dossier du projet ; PyCharm détecte `.venv` (sinon :
   Settings → Project → Python Interpreter → Existing → `.venv\Scripts\python.exe`).
2. Run/Debug Configuration → module `tei_reader`, paramètres :
   `render samples\prose.xml --open`, `view samples\prose.xml` ou `gui`.
3. Les tests se lancent par clic droit sur `tests/` → Run pytest.

## État actuel du prototype

**Ce qui est stable** : le contrat HTML central et sa synchronisation
XSLT/Python testée ; le parsing sécurisé par lxml ; la transformation
SaxonC ; les profils `prose`, `verse`, `drama`, `correspondence` et
`diagnostic` ; les notes inline ou en fin de document ; l'apparat minimal
sans perte de variantes ; la correspondance ; les images locales relatives
sécurisées ; les éléments de transcription (`add`, `del`, `subst`,
`choice`, etc.) ; les éléments savants communs (`date`, `name`,
`persName`, `placeName`, `orgName`, `title`, `term`, `ref`, `ptr`) ; la
tokenisation et les structures fréquentes (`w`, `c`, `pc`, `seg`, `ab`,
`milestone`, `fw`, `div1`, `div2`) ; l'audit des fixtures ; les snapshots
HTML ; la CLI ; l'interface desktop pywebview expérimentale.

**Ce qui reste expérimental ou à faire** : les notes marginales
flottantes ; un vrai mode « copie des médias » pour produire un dossier
HTML transportable ; les réglages fins par corpus ou fichier ; une
interface d'apparat critique ; la gestion savante de `sound`, `interp`,
`interpGrp`, `event`, `relation`, `desc` ; la performance sur très gros
fichiers ; le packaging exécutable ; la portabilité future vers Firefox.

**Portable vers Firefox** : le contrat HTML (classes `tei-*`, `data-tei-*`,
distinction natif/fallback), les profils JSON, toutes les CSS, le corpus
d'échantillons et les assertions des tests.

**Spécifique au prototype Python** : la XSLT et SaxonC (moteur remplaçable
derrière `TransformEngine`), l'analyse lxml, la CLI, pywebview.

## Limites techniques connues

- SaxonC s'exécute dans le processus principal (appel direct) ;
  l'isolation en sous-processus viendra si les crashs natifs ou le
  packaging le justifient — l'interface `TransformEngine` est prévue pour.
- Le packaging en exécutable (PyInstaller/Nuitka) n'est pas couvert :
  saxonche embarque une bibliothèque native qui demande des hooks manuels.
  Installation par `pip` recommandée.
