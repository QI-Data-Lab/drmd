<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:drmd="https://example.org/drmd"
    xmlns:dcc="https://ptb.de/dcc"
    xmlns:si="https://ptb.de/si"
    xmlns:ds="http://www.w3.org/2000/09/xmldsig#">

    <!-- Output method as HTML -->
    <xsl:output method="html" indent="yes" />

    <!-- Root template -->
    <xsl:template match="/">
        <html>
            <head>
                <title><xsl:value-of select="drmd:digitalReferenceMaterialDocument/drmd:administrativeData/drmd:coreData/drmd:titleOfTheDocument" /></title>
                <style>
                    body { font-family: Arial, sans-serif; }
                    table { width: 100%; border-collapse: collapse; margin-bottom: 20px; }
                    th, td { border: 1px solid #ddd; padding: 8px; }
                    th { background-color: #f2f2f2; text-align: left; }
                    h1, h2, h3 { color: #333; }
                    .divider { margin: 20px 0; border-top: 1px solid #ddd; }
                </style>
            </head>
            <body>
                <h1><xsl:value-of select="drmd:digitalReferenceMaterialDocument/drmd:administrativeData/drmd:coreData/drmd:titleOfTheDocument" /></h1>
                <xsl:apply-templates select="drmd:digitalReferenceMaterialDocument" />
            </body>
        </html>
    </xsl:template>

    <!-- Template for the root element -->
    <xsl:template match="drmd:digitalReferenceMaterialDocument">
        <h2>Administrative Data</h2>
        <xsl:apply-templates select="drmd:administrativeData" />
        <div class="divider"></div>
        <h2>Measurement Results</h2>
        <xsl:apply-templates select="drmd:measurementResults" />
    </xsl:template>

    <!-- Template for administrative data -->
    <xsl:template match="drmd:administrativeData">
        <h3>Core Data</h3>
        <table>
            <tr><th>Title</th><td><xsl:value-of select="drmd:coreData/drmd:titleOfTheDocument" /></td></tr>
            <tr><th>Unique Identifier</th><td><xsl:value-of select="drmd:coreData/drmd:uniqueIdentifier" /></td></tr>
            <tr><th>Period of Validity</th><td><xsl:value-of select="drmd:coreData/drmd:periodOfValidity" /></td></tr>
            <tr><th>Date of Issue</th><td><xsl:value-of select="drmd:coreData/drmd:dataOfIssue" /></td></tr>
            <tr><th>Date of Certificate Approval</th><td><xsl:value-of select="drmd:coreData/drmd:dateOfCertificateApproval" /></td></tr>
        </table>

        <h3>Reference Material Producer</h3>
        <table>
            <tr><th>Name</th><td><xsl:value-of select="drmd:referenceMaterialProducer/drmd:name" /></td></tr>
            <tr><th>Contact</th>
                <td>
                    <xsl:value-of select="drmd:referenceMaterialProducer/drmd:contact/dcc:location/dcc:street" />,
                    <xsl:value-of select="drmd:referenceMaterialProducer/drmd:contact/dcc:location/dcc:streetNo" /><br/>
                    <xsl:value-of select="drmd:referenceMaterialProducer/drmd:contact/dcc:location/dcc:postCode" />
                    <xsl:value-of select="drmd:referenceMaterialProducer/drmd:contact/dcc:location/dcc:city" />
                    <xsl:value-of select="drmd:referenceMaterialProducer/drmd:contact/dcc:location/dcc:countryCode" /><br/>
                    <xsl:text>Phone: </xsl:text><xsl:value-of select="drmd:referenceMaterialProducer/drmd:contact/dcc:phone" /><br/>
                    <xsl:text>Fax: </xsl:text><xsl:value-of select="drmd:referenceMaterialProducer/drmd:contact/dcc:fax" /><br/>
                    <xsl:text>Email: </xsl:text><xsl:value-of select="drmd:referenceMaterialProducer/drmd:contact/dcc:eMail" /><br/>
                </td>
            </tr>
        </table>

        <h3>Items</h3>
        <xsl:apply-templates select="drmd:items/drmd:item" />

        <h3>Statements</h3>
        <xsl:apply-templates select="drmd:statements" />

        <h3>Responsible Persons</h3>
        <table>
            <tr><th>Name</th><th>Role</th></tr>
            <xsl:for-each select="drmd:respPersons/dcc:respPerson">
                <tr>
                    <td><xsl:value-of select="dcc:person/dcc:name" /></td>
                    <td><xsl:value-of select="dcc:person/dcc:role" /></td>
                </tr>
            </xsl:for-each>
        </table>
    </xsl:template>

    <!-- Template for items -->
    <xsl:template match="drmd:item">
        <table>
            <tr><th>Name</th><td><xsl:value-of select="drmd:name/dcc:content[@lang='en']" /></td></tr>
            <tr><th>Description</th>
                <td>
                    <xsl:for-each select="drmd:description/dcc:content[@lang='en']">
                        <xsl:value-of select="." /><br/>
                    </xsl:for-each>
                </td>
            </tr>
            <tr><th>Minimum Sample Size</th>
                <td>
                    <xsl:for-each select="drmd:minimumSampleSize/dcc:itemQuantity/si:realListXMLList">
                        <xsl:value-of select="si:valueXMLList" /><xsl:text> </xsl:text><xsl:value-of select="si:unitXMLList" /><br/>
                    </xsl:for-each>
                </td>
            </tr>
        </table>
    </xsl:template>

    <!-- Template for statements -->
    <xsl:template match="drmd:statements">
<!--        <table>
            <tr><th>Name</th><th>Content</th></tr>
            <xsl:for-each select="*">
                <tr>
                    <td><xsl:value-of select="dcc:name/dcc:content[@lang='en']" /></td>
                    <td>
                        <xsl:for-each select="dcc:description/dcc:content[@lang='en']">
                            <xsl:value-of select="." /><br/>
                        </xsl:for-each>
                    </td>
                </tr>
            </xsl:for-each>
        </table>
-->
    <xsl:for-each select="*">
        <h4><xsl:value-of select="dcc:name/dcc:content[@lang='en']" /></h4>
        <p>
            <xsl:for-each select="dcc:description/dcc:content[@lang='en']">
                <xsl:value-of select="." /><br/>
            </xsl:for-each>
        </p>
    </xsl:for-each>
</xsl:template>


<!-- Template for measurement results -->
<xsl:template match="drmd:measurementResults">
    <xsl:apply-templates select="dcc:results/dcc:result" />
</xsl:template>

<!-- Template for results -->
<xsl:template match="dcc:result">
    <h3><xsl:value-of select="dcc:name/dcc:content[@lang='en']" /></h3>
    <p><xsl:value-of select="dcc:description/dcc:content[@lang='en']" /></p>
    <table>
        <tr>
            <th>Property</th>
            <th>Property Value</th>
            <th>Property Unit</th>
            <th>Uncertainty Value</th>
            <th>Uncertainty Unit</th>
        </tr>
        <xsl:for-each select="dcc:data/dcc:list">
            <tr>
                <td><xsl:value-of select="dcc:description/dcc:content[@lang='en']" /></td>
                <td>
                    <xsl:for-each select="dcc:quantity[@refType='basic_measuredValue']/si:realListXMLList/si:valueXMLList">
                        <xsl:value-of select="." /><br />
                    </xsl:for-each>
                </td>
                <td>
                    <xsl:for-each select="dcc:quantity[@refType='basic_measuredValue']/si:realListXMLList/si:unitXMLList">
                        <xsl:value-of select="." /><br />
                    </xsl:for-each>
                </td>
                <td>
                    <xsl:for-each select="dcc:quantity[@refType='basic_measurementError']/si:realListXMLList/si:valueXMLList">
                        <xsl:value-of select="." /><br />
                    </xsl:for-each>
                </td>
                <td>
                    <xsl:for-each select="dcc:quantity[@refType='basic_measurementError']/si:realListXMLList/si:unitXMLList">
                        <xsl:value-of select="." /><br />
                    </xsl:for-each>
                </td>
            </tr>
        </xsl:for-each>
    </table>
    <hr />
</xsl:template>

</xsl:stylesheet>
