from fpdf import FPDF

pdf = FPDF()
pdf.add_page()
pdf.set_font("Arial", size=12)

content = """
Artificial Intelligence (AI) refers to the simulation of human intelligence in machines that are programmed to think like humans and mimic their actions. The term may also be applied to any machine that exhibits traits associated with a human mind such as learning and problem-solving.

The ideal characteristic of artificial intelligence is its ability to rationalize and take actions that have the best chance of achieving a specific goal. A subset of artificial intelligence is machine learning (ML), which refers to the concept that computer programs can automatically learn from and adapt to new data without being assisted by humans. Deep learning techniques enable this automatic learning through the absorption of huge amounts of unstructured data such as text, images, or video.

In the 1950s, Alan Turing explored the mathematical possibility of artificial intelligence. He suggested that humans use available information as well as reason in order to solve problems and make decisions, so why can't machines do the same thing? This led to the Turing Test, a measure of machine intelligence.
"""

# Title
pdf.set_font("Arial", 'B', 16)
pdf.cell(200, 10, text="A Brief History of Artificial Intelligence", new_x='LMARGIN', new_y='NEXT', align='C')

# Content
pdf.set_font("Arial", size=12)
pdf.multi_cell(0, 10, text=content)

# Save
pdf.output("data/ai_history.pdf")
print("PDF created successfully at data/ai_history.pdf!")
