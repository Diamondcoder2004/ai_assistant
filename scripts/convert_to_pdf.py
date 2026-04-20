import comtypes.client
import os

# Input and output paths
input_pptx = r'd:\ai_assistant\practice\О_заказчике_Башкирэнерго.pptx'
output_pdf = r'd:\ai_assistant\practice\О_заказчике_Башкирэнерго.pdf'

# Create PowerPoint application
powerpoint = comtypes.client.CreateObject("Powerpoint.Application")
powerpoint.Visible = 1

# Open presentation
presentation = powerpoint.Presentations.Open(input_pptx)

# Save as PDF
presentation.SaveAs(output_pdf, 32)  # 32 = PDF format

# Close presentation and quit
presentation.Close()
powerpoint.Quit()

print(f'✓ PDF создан: {output_pdf}')
