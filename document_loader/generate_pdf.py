######################################################################
### This file generates a dummy pdf file to be used for the example ##
######################################################################

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
 
def create_sample_privacy_policy(output_file="document_loader/docs/test_privacy_policy.pdf"):
    # Create the document
    doc = SimpleDocTemplate(
        output_file,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    # Container for content
    elements = []
    
    # Styles
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='MainTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=1  # Center alignment
    ))
    styles.add(ParagraphStyle(
        name='SectionTitle',
        parent=styles['Heading2'],
        fontSize=14,
        spaceBefore=20,
        spaceAfter=12
    ))
    styles.add(ParagraphStyle(
        name='NormalText',
        parent=styles['Normal'],
        fontSize=11,
        spaceBefore=6,
        spaceAfter=12
    ))
    
    # Document Title
    elements.append(Paragraph("Corporate Data Protection and Privacy Policy", styles['MainTitle']))
    elements.append(Spacer(1, 30))
    
    # Document Reference
    elements.append(Paragraph("Document Reference: POL-DP-2024-001", styles['NormalText']))
    elements.append(Paragraph("Version: 1.0", styles['NormalText']))
    elements.append(Paragraph("Last Updated: January 14, 2024", styles['NormalText']))
    elements.append(Spacer(1, 30))
    
    # Content sections
    sections = [
        {
            'title': "1. Executive Summary",
            'content': """This policy establishes the framework for data protection and privacy compliance within our organization. It outlines key requirements under GDPR (Regulation (EU) 2016/679), CCPA (California Civil Code § 1798.100), and other applicable privacy laws. All employees, contractors, and third-party processors must comply with this policy."""
        },
        {
            'title': "2. Scope and Applicability",
            'content': """2.1. This policy applies to all processing of personal data within [Organization Name], including:
            
• Employee personal information
• Customer data
• Vendor and supplier information
• Marketing databases
• Website visitor data
 
2.2. Territorial Scope: This policy applies to data processing activities:
• Within the European Union
• Related to offering goods/services to EU residents
• Related to monitoring behavior of EU residents
• Within California for CCPA compliance
• In other jurisdictions where privacy laws apply"""
        },
        {
            'title': "3. Legal Framework",
            'content': """This policy complies with multiple regulatory frameworks, including:
 
3.1. European Union:
• General Data Protection Regulation (GDPR)
• ePrivacy Directive 2002/58/EC
 
3.2. United States:
• California Consumer Privacy Act (CCPA)
• California Privacy Rights Act (CPRA)
• Virginia Consumer Data Protection Act (VCDPA)
 
3.3. Industry-Specific Regulations:
• Health Insurance Portability and Accountability Act (HIPAA)
• Gramm-Leach-Bliley Act (GLBA)
 
Reference: Article 5 GDPR for core principles; Section 1798.100 CCPA for consumer rights."""
        },
        {
            'title': "4. Data Protection Principles",
            'content': """As per Article 5(1) GDPR and related regulations, all personal data must be:
 
4.1. Processed lawfully, fairly, and transparently
• Clear legal basis for processing
• Transparent privacy notices
• Fair processing practices
 
4.2. Collected for specified, explicit, and legitimate purposes
• Clear purpose limitation
• No secondary processing without consent
• Documented business purposes
 
4.3. Data minimization
• Only necessary data collected
• Regular data audits
• Privacy by design implementation
 
4.4. Accuracy
• Regular data verification
• Correction procedures
• Data quality monitoring
 
Reference: See Article 5 GDPR; 15 U.S.C. § 6801-6809 for financial privacy requirements."""
        },
        {
            'title': "5. Security Requirements",
            'content': """5.1. Technical Measures
• Encryption at rest and in transit
• Access controls and authentication
• Regular security assessments
• Intrusion detection systems
 
5.2. Organizational Measures
• Staff training requirements
• Security policies and procedures
• Incident response plans
• Regular compliance audits
 
Reference: Article 32 GDPR for security requirements; 45 CFR § 164.306 for HIPAA security standards."""
        },
        {
            'title': "6. Data Breach Response",
            'content': """6.1. Breach Notification Requirements:
 
• EU: Within 72 hours to supervisory authority (Article 33 GDPR)
• California: Without unreasonable delay (CCPA § 1798.82)
• HIPAA: Within 60 days of discovery
 
6.2. Response Procedures:
• Immediate containment measures
• Investigation and documentation
• Notification to affected individuals
• Remediation planning
 
Reference: Article 33-34 GDPR; California Civil Code 1798.82."""
        },
        {
            'title': "7. Individual Rights",
            'content': """7.1. Rights under GDPR:
• Right to access
• Right to rectification
• Right to erasure
• Right to data portability
• Right to object
 
7.2. Rights under CCPA:
• Right to know
• Right to delete
• Right to opt-out
• Right to non-discrimination
 
Response timeframes:
• GDPR: One month (Article 12)
• CCPA: 45 days (§ 1798.130)"""
        },
        {
            'title': "8. Compliance Measures",
            'content': """8.1. Documentation Requirements:
• Records of processing activities
• Data Protection Impact Assessments
• Consent records
• Data transfer agreements
 
8.2. Training Requirements:
• Annual privacy training
• Role-specific security training
• Incident response drills
• Compliance updates
 
Reference: Article 30 GDPR for documentation; 45 CFR § 164.308 for training requirements."""
        },
        {
            'title': "9. International Data Transfers",
            'content': """9.1. Transfer Mechanisms:
• Standard Contractual Clauses
• Binding Corporate Rules
• Adequacy decisions
• Specific derogations
 
9.2. Requirements:
• Data transfer impact assessments
• Additional safeguards
• Documentation of transfers
• Regular review of mechanisms
 
Reference: Chapter V GDPR; Article 44-50 for international transfers."""
        }
    ]
    
    # Add sections to document
    for section in sections:
        elements.append(Paragraph(section['title'], styles['SectionTitle']))
        elements.append(Paragraph(section['content'], styles['NormalText']))
    
    # Build the PDF
    doc.build(elements)
    return output_file
 
if __name__ == '__main__':
    output_file = create_sample_privacy_policy()
    print(f"Successfully generated {output_file}")
