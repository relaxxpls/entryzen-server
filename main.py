import gradio as gr
from src.parse_pdf import parse_pdf


iface = gr.Interface(
    fn=parse_pdf,
    inputs=gr.File(label="Upload Invoice PDF"),
    outputs=[
        gr.Dataframe(label="Invoice Details"),
        gr.Dataframe(label="Invoice Items"),
    ],
    title="Invoice Processor",
    description="Upload a PDF invoice to extract common data and item details.",
)

# Launch the app
iface.launch(share=True)
