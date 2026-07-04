<?xml version="1.0" encoding="UTF-8"?>
<!--
  tei-common.xsl : transformation TEI -> HTML5 (étape 1).
  Contrat HTML documenté dans docs/contrat-html.md — c'est la référence.
  La liste des éléments traités ici doit rester synchronisée avec
  HANDLED_ELEMENTS dans tei_reader/core/document.py ; cette synchronisation
  est vérifiée automatiquement par tests/test_contract_sync.py.
-->
<xsl:stylesheet version="3.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:tei="http://www.tei-c.org/ns/1.0"
    exclude-result-prefixes="tei">

  <xsl:output method="html" html-version="5" encoding="utf-8" indent="no"/>

  <xsl:param name="css-hrefs" select="'base.css'"/>
  <xsl:param name="show-pb" select="'true'"/>
  <xsl:param name="note-mode" select="'inline'"/> <!-- 'inline' | 'end' -->
  <xsl:param name="doc-title-fallback" select="'Document TEI'"/>

  <!-- Médias locaux vérifiés côté Python (core/document.py) : la XSLT ne
       sait pas tester l'existence d'un fichier. existing-media = valeurs
       de graphic/@url et pb/@facs trouvées sur disque, séparées par des
       sauts de ligne ; media-base = dossier du fichier source (URI file:),
       car le HTML est écrit dans un autre dossier. Vide = aucun média. -->
  <xsl:param name="existing-media" select="''"/>
  <xsl:param name="media-base" select="''"/>
  <xsl:variable name="existing-media-set"
      select="tokenize($existing-media, '&#10;')[. != '']"/>

  <!-- ======================= Document ======================= -->

  <xsl:template match="/">
    <html>
      <head>
        <meta charset="utf-8"/>
        <!-- 'self' est inopérant sous file:// (origine opaque) : on autorise
             explicitement le schéma file: pour styles et images ; les scripts
             restent interdits par default-src 'none'. -->
        <meta http-equiv="Content-Security-Policy"
              content="default-src 'none'; style-src 'self' file:; img-src 'self' file:"/>
        <title>
          <xsl:variable name="t"
              select="normalize-space((//tei:teiHeader//tei:titleStmt/tei:title)[1])"/>
          <xsl:value-of select="if ($t != '') then $t else $doc-title-fallback"/>
        </title>
        <xsl:for-each select="tokenize(normalize-space($css-hrefs), ' ')">
          <link rel="stylesheet" href="{.}"/>
        </xsl:for-each>
      </head>
      <body>
        <xsl:apply-templates/>
      </body>
    </html>
  </xsl:template>

  <xsl:template match="tei:TEI | tei:teiCorpus">
    <xsl:apply-templates select="tei:text | tei:TEI"/>
  </xsl:template>

  <!-- Le teiHeader n'est pas rendu (titre extrait ci-dessus).
       facsimile/standOff : hors rendu à ce stade, signalés par les
       diagnostics Python. -->
  <xsl:template match="tei:teiHeader | tei:facsimile | tei:standOff"/>

  <!-- ================== Attributs partagés =================== -->
  <!-- class = tei-<nom> [+ classes] [+ rend-<valeur>...]
       @xml:id -> id ; @xml:lang -> lang ;
       attributs savants -> data-tei-<nom> (liste : voir contrat HTML). -->

  <xsl:variable name="data-attributes"
      select="('type','subtype','n','place','ana','ref','corresp','facs',
               'rend','wit','target','url','who','met','part')"/>

  <xsl:template name="data-atts">
    <xsl:for-each select="@*[local-name() = $data-attributes
                             and namespace-uri() = '']">
      <xsl:attribute name="data-tei-{local-name()}" select="."/>
    </xsl:for-each>
  </xsl:template>

  <xsl:template name="tei-atts">
    <xsl:param name="classes" select="()"/>
    <xsl:attribute name="class"
        select="string-join((concat('tei-', local-name()),
                             $classes,
                             for $r in tokenize(normalize-space(@rend), ' ')
                               return concat('rend-', $r)), ' ')"/>
    <xsl:if test="@xml:id">
      <xsl:attribute name="id" select="@xml:id"/>
    </xsl:if>
    <xsl:if test="@xml:lang">
      <xsl:attribute name="lang" select="@xml:lang"/>
    </xsl:if>
    <xsl:call-template name="data-atts"/>
  </xsl:template>

  <!-- ===================== Structure ========================= -->

  <xsl:template match="tei:text">
    <main>
      <xsl:call-template name="tei-atts"/>
      <xsl:apply-templates/>
      <xsl:if test="$note-mode = 'end' and .//tei:note">
        <xsl:call-template name="endnotes"/>
      </xsl:if>
    </main>
  </xsl:template>

  <xsl:template match="tei:front | tei:body | tei:back">
    <div>
      <xsl:call-template name="tei-atts"/>
      <xsl:apply-templates/>
    </div>
  </xsl:template>

  <xsl:template match="tei:div">
    <section>
      <xsl:call-template name="tei-atts"/>
      <xsl:apply-templates/>
    </section>
  </xsl:template>

  <xsl:template match="tei:head">
    <xsl:variable name="level" select="min((count(ancestor::tei:div) + 1, 6))"/>
    <xsl:element name="h{$level}">
      <xsl:call-template name="tei-atts"/>
      <xsl:apply-templates/>
    </xsl:element>
  </xsl:template>

  <xsl:template match="tei:p">
    <p>
      <xsl:call-template name="tei-atts"/>
      <xsl:apply-templates/>
    </p>
  </xsl:template>

  <!-- ================ Mise en relief, inline ================= -->

  <xsl:template match="tei:hi | tei:foreign | tei:quote | tei:q">
    <span>
      <xsl:call-template name="tei-atts"/>
      <xsl:apply-templates/>
    </span>
  </xsl:template>

  <xsl:template match="tei:emph">
    <em>
      <xsl:call-template name="tei-atts"/>
      <xsl:apply-templates/>
    </em>
  </xsl:template>

  <!-- ===================== Notes ============================= -->
  <!-- Deux modes (paramètre note-mode) :
       - inline : la note est rendue sur place dans un span ;
       - end    : appel de note numéroté, notes regroupées en fin de
                  document dans <section class="tei-notes">.
       Le numéro affiché est @n si présent, sinon le rang de la note
       dans le <text>. -->

  <xsl:template match="tei:note">
    <xsl:choose>
      <xsl:when test="$note-mode = 'end'">
        <a class="tei-note-ref" href="#note-{generate-id()}"
           id="noteref-{generate-id()}">
          <sup>
            <xsl:call-template name="note-marker"/>
          </sup>
        </a>
      </xsl:when>
      <xsl:otherwise>
        <span>
          <xsl:call-template name="tei-atts"/>
          <xsl:apply-templates/>
        </span>
      </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template name="note-marker">
    <xsl:value-of
        select="if (@n) then string(@n)
                else string(count(preceding::tei:note[ancestor::tei:text]) + 1)"/>
  </xsl:template>

  <xsl:template name="endnotes">
    <section class="tei-notes">
      <h2 class="tei-notes-head">Notes</h2>
      <ol class="tei-notes-list">
        <xsl:for-each select=".//tei:note">
          <li class="tei-note" id="note-{generate-id()}">
            <xsl:call-template name="data-atts"/>
            <span class="tei-note-marker">
              <xsl:call-template name="note-marker"/>
              <xsl:text>.</xsl:text>
            </span>
            <xsl:text> </xsl:text>
            <xsl:apply-templates/>
            <xsl:text> </xsl:text>
            <a class="tei-note-backlink" href="#noteref-{generate-id()}">&#8617;</a>
          </li>
        </xsl:for-each>
      </ol>
    </section>
  </xsl:template>

  <!-- ================= Sauts de page / ligne ================= -->

  <xsl:template match="tei:lb">
    <br class="tei-lb"/>
  </xsl:template>

  <!-- Saut de page : span vide (marqueur en CSS). Si @facs désigne un
       fichier local existant, le marqueur devient un lien <a> vers le
       fac-similé — même classe tei-pb, les CSS restent valables. -->
  <xsl:template match="tei:pb">
    <xsl:if test="$show-pb = 'true'">
      <xsl:choose>
        <xsl:when test="@facs = $existing-media-set">
          <a href="{$media-base}/{@facs}">
            <xsl:call-template name="tei-atts">
              <xsl:with-param name="classes" select="'tei-pb-facs'"/>
            </xsl:call-template>
          </a>
        </xsl:when>
        <xsl:otherwise>
          <span>
            <xsl:call-template name="tei-atts"/>
          </span>
        </xsl:otherwise>
      </xsl:choose>
    </xsl:if>
  </xsl:template>

  <!-- ====================== Poésie ============================ -->
  <!-- lg : bloc strophique (@type conservé) ; l : vers (@n, @met,
       @part conservés ; numérotation et indentations en CSS). -->

  <xsl:template match="tei:lg">
    <div>
      <xsl:call-template name="tei-atts"/>
      <xsl:apply-templates/>
    </div>
  </xsl:template>

  <xsl:template match="tei:l">
    <span>
      <xsl:call-template name="tei-atts"/>
      <xsl:apply-templates/>
    </span>
  </xsl:template>

  <!-- ====================== Théâtre =========================== -->
  <!-- Actes et scènes : ce sont des tei:div ordinaires ; leur @type
       (act, scene) est conservé en data-tei-type et ciblé par drama.css. -->

  <xsl:template match="tei:sp">
    <div>
      <xsl:call-template name="tei-atts"/>
      <xsl:apply-templates/>
    </div>
  </xsl:template>

  <xsl:template match="tei:speaker">
    <span>
      <xsl:call-template name="tei-atts"/>
      <xsl:apply-templates/>
    </span>
  </xsl:template>

  <xsl:template match="tei:stage">
    <span>
      <xsl:call-template name="tei-atts"/>
      <xsl:apply-templates/>
    </span>
  </xsl:template>

  <xsl:template match="tei:castList">
    <div>
      <xsl:call-template name="tei-atts"/>
      <xsl:apply-templates/>
    </div>
  </xsl:template>

  <xsl:template match="tei:castItem">
    <div>
      <xsl:call-template name="tei-atts"/>
      <xsl:apply-templates/>
    </div>
  </xsl:template>

  <xsl:template match="tei:role | tei:roleDesc">
    <span>
      <xsl:call-template name="tei-atts"/>
      <xsl:apply-templates/>
    </span>
  </xsl:template>

  <!-- =================== Correspondance ======================= -->
  <!-- Rendu minimal d'une lettre : en-tête (opener), formule finale
       (closer), date/lieu (dateline), salutation (salute), signature
       (signed), adresse (address/addrLine). La mise en page (alignements,
       italiques) est entièrement en CSS (correspondence.css). -->

  <xsl:template match="tei:opener | tei:closer | tei:address">
    <div>
      <xsl:call-template name="tei-atts"/>
      <xsl:apply-templates/>
    </div>
  </xsl:template>

  <xsl:template match="tei:dateline | tei:salute | tei:signed | tei:addrLine">
    <span>
      <xsl:call-template name="tei-atts"/>
      <xsl:apply-templates/>
    </span>
  </xsl:template>

  <!-- ============ Apparat critique : rendu minimal ============ -->
  <!-- Décision éditoriale (documentée dans le contrat HTML) :
       - le texte des variantes n'est JAMAIS perdu : lem et rdg sont
         toujours émis dans le HTML ; leur visibilité est pilotée par CSS ;
       - en lecture courante (base.css), seuls lem et tei-rdg-default
         sont visibles ;
       - si un app n'a pas de lem, le premier rdg reçoit la classe
         tei-rdg-default afin que le texte reste lisible. -->

  <xsl:template match="tei:app">
    <span>
      <xsl:call-template name="tei-atts"/>
      <xsl:apply-templates/>
    </span>
  </xsl:template>

  <xsl:template match="tei:lem">
    <span>
      <xsl:call-template name="tei-atts"/>
      <xsl:apply-templates/>
    </span>
  </xsl:template>

  <xsl:template match="tei:rdg">
    <span>
      <xsl:call-template name="tei-atts">
        <xsl:with-param name="classes"
            select="if (empty(../tei:lem) and empty(preceding-sibling::tei:rdg))
                    then 'tei-rdg-default' else ()"/>
      </xsl:call-template>
      <xsl:apply-templates/>
    </span>
  </xsl:template>

  <!-- ================ Témoins (listWit/witness) =============== -->

  <xsl:template match="tei:listWit">
    <div>
      <xsl:call-template name="tei-atts"/>
      <xsl:apply-templates/>
    </div>
  </xsl:template>

  <xsl:template match="tei:witness">
    <div>
      <xsl:call-template name="tei-atts"/>
      <xsl:apply-templates/>
    </div>
  </xsl:template>

  <!-- ============= Fac-similés : images locales ================ -->
  <!-- @url existant sur disque -> vraie <img> (src absolu file: vers le
       dossier source) ; sinon marqueur textuel + diagnostic missing-media
       côté Python. Aucune ressource distante n'est jamais chargée. -->

  <xsl:template match="tei:graphic">
    <span>
      <xsl:call-template name="tei-atts"/>
      <xsl:choose>
        <xsl:when test="@url = $existing-media-set">
          <img class="tei-graphic-img" src="{$media-base}/{@url}"
               alt="{@url}"/>
        </xsl:when>
        <xsl:otherwise>
          <xsl:text>[image : </xsl:text>
          <xsl:value-of select="@url"/>
          <xsl:text>]</xsl:text>
        </xsl:otherwise>
      </xsl:choose>
    </span>
  </xsl:template>

  <!-- ===================== Fallback =========================== -->
  <!-- Tout élément TEI non traité reste lisible : span neutre,
       nom conservé dans data-tei, attributs savants conservés. -->

  <xsl:template match="tei:*" priority="-5">
    <span data-tei="{local-name()}">
      <xsl:attribute name="class"
          select="string-join(('tei-unhandled',
                               for $r in tokenize(normalize-space(@rend), ' ')
                                 return concat('rend-', $r)), ' ')"/>
      <xsl:if test="@xml:id"><xsl:attribute name="id" select="@xml:id"/></xsl:if>
      <xsl:if test="@xml:lang"><xsl:attribute name="lang" select="@xml:lang"/></xsl:if>
      <xsl:call-template name="data-atts"/>
      <xsl:apply-templates/>
    </span>
  </xsl:template>

  <!-- Élément hors espace de noms TEI -->
  <xsl:template match="*" priority="-6">
    <span class="tei-unhandled non-tei" data-tei="{name()}"
          data-tei-ns="{namespace-uri()}">
      <xsl:apply-templates/>
    </span>
  </xsl:template>

</xsl:stylesheet>
