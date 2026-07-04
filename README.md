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

# Transformer et ouvrir dans le navigateur par défaut
.\.venv\Scripts\tei-reader render samples\prose.xml --open

# Transformer et afficher dans une fenêtre webview
.\.venv\Scripts\tei-reader view samples\drama.xml --profile drama

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

Quatre profils, définis dans `tei_reader/resources/profiles/` :

- **prose** — lecture courante (roman, essai, correspondance) : notes en
  fin de document, apparat réduit à la leçon retenue ;
- **verse** — poésie : strophes, numéros de vers dans la marge, vers
  partagés (`@part`) en retrait ;
- **drama** — théâtre : actes/scènes centrés, locuteurs en petites
  capitales, didascalies distinctes, distribution encadrée ;
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
├── ui/webview_app.py       # fenêtre pywebview minimale
└── resources/
    ├── xsl/tei-common.xsl  # transformation TEI → HTML5 (contrat HTML)
    ├── css/                # base.css, diagnostic.css
    └── profiles/           # prose.json, diagnostic.json
samples/                    # corpus de test (prose, élément inconnu, mal formé)
tests/                      # pytest
docs/                       # architecture, contrat HTML
```

## Tests

```powershell
.\.venv\Scripts\python -m pytest
```

Les tests garantissent au minimum : un TEI simple produit du HTML conforme au
contrat ; un élément inconnu ne fait pas planter la transformation ; les
diagnostics sont produits ; un XML mal formé échoue proprement (pas d'exception,
un `RenderResult` d'erreur).

## Lancer depuis PyCharm

1. Ouvrir le dossier du projet ; PyCharm détecte `.venv` (sinon :
   Settings → Project → Python Interpreter → Existing → `.venv\Scripts\python.exe`).
2. Run/Debug Configuration → module `tei_reader`, paramètres :
   `render samples\prose.xml --open` (ou `view samples\prose.xml`).
3. Les tests se lancent par clic droit sur `tests/` → Run pytest.

## État de l'étape 1

**Ce qui marche** : prose, poésie (strophes, vers numérotés, vers partagés,
métrique conservée), théâtre (actes, scènes, locuteurs, didascalies,
distribution), notes en deux modes (inline / fin de document), apparat
critique minimal sans perte de texte, témoins, fallback lisible pour tout
élément inconnu, diagnostics enrichis (résumé chiffré, références locales
cassées, images manquantes), commande `inspect`, synchronisation
XSLT/Python vérifiée par test.

**Volontairement minimal** : apparat linéaire (pas d'interface critique) ;
fac-similés en simple marqueur ; notes marginales rendues comme les autres
(l'attribut `place` est conservé pour plus tard) ; correspondance
(opener/closer/dateline) pas encore traitée — fallback lisible en attendant.

**Reste à faire** : module correspondance ; affichage des images locales ;
notes marginales flottantes ; cascade de réglages (corpus/fichier) ;
rechargement à chaud dans l'UI ; snapshots de non-régression ; test de
performance sur un gros fichier.

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
