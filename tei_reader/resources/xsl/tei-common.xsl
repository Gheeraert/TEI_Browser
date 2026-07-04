<?xml version="1.0" encoding="UTF-8"?>
<!--
  tei-common.xsl : feuille de transformation minimale TEI -> HTML5 (étape 0).
  Contrat HTML documenté dans docs/contrat-html.md.
  La liste des éléments traités ici doit rester synchronisée avec
  HANDLED_ELEMENTS dans tei_reader/core/document.py.
-->
<xsl:stylesheet version="3.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:tei="http://www.tei-c.org/ns/1.0"
    exclude-result-prefixes="tei">

  <xsl:output method="html" html-version="5" encoding="utf-8" indent="no"/>

  <xsl:param name="css-hrefs" select="'base.css'"/>
  <xsl:param name="show-pb" select="'true'"/>
  <xsl:param name="doc-title-fallback" select="'Document TEI'"/>

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
       facsimile/standOff : hors rendu à l'étape 0, signalés par les diagnostics Python. -->
  <xsl:template match="tei:teiHeader | tei:facsimile | tei:standOff"/>

  <!-- ================== Attributs partagés =================== -->
  <!-- class = tei-<nom> [+ classes] [+ rend-<valeur>...]
       @xml:id -> id ; @xml:lang -> lang ;
       attributs savants -> data-tei-<nom>. -->
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
    <xsl:for-each select="@type | @subtype | @n | @place | @ana | @ref
                          | @corresp | @facs | @rend | @wit | @target | @url">
      <xsl:attribute name="data-tei-{local-name()}" select="."/>
    </xsl:for-each>
  </xsl:template>

  <!-- ===================== Structure ========================= -->

  <xsl:template match="tei:text">
    <main>
      <xsl:call-template name="tei-atts"/>
      <xsl:apply-templates/>
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

  <xsl:template match="tei:note">
    <span>
      <xsl:call-template name="tei-atts"/>
      <xsl:apply-templates/>
    </span>
  </xsl:template>

  <!-- ================= Sauts de page / ligne ================= -->

  <xsl:template match="tei:lb">
    <br class="tei-lb"/>
  </xsl:template>

  <xsl:template match="tei:pb">
    <xsl:if test="$show-pb = 'true'">
      <span>
        <xsl:call-template name="tei-atts"/>
      </span>
    </xsl:if>
  </xsl:template>

  <!-- ====================== Vers ============================= -->

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

  <!-- ========== Apparat critique : rendu linéaire minimal ===== -->
  <!-- Décision étape 0 : app/lem/rdg reconnus, rendu simple lisible ;
       la visibilité des rdg est pilotée par CSS (profil diagnostic). -->

  <xsl:template match="tei:app">
    <span>
      <xsl:call-template name="tei-atts"/>
      <xsl:apply-templates/>
    </span>
  </xsl:template>

  <xsl:template match="tei:lem | tei:rdg">
    <span>
      <xsl:call-template name="tei-atts"/>
      <xsl:apply-templates/>
    </span>
  </xsl:template>

  <!-- ========== Fac-similés : simple marqueur (étape 0) ======= -->

  <xsl:template match="tei:graphic">
    <span>
      <xsl:call-template name="tei-atts"/>
      <xsl:text>[image : </xsl:text>
      <xsl:value-of select="@url"/>
      <xsl:text>]</xsl:text>
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
      <xsl:for-each select="@type | @subtype | @n | @place | @ana | @ref
                            | @corresp | @facs | @rend | @wit | @target | @url">
        <xsl:attribute name="data-tei-{local-name()}" select="."/>
      </xsl:for-each>
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
