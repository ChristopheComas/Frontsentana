import streamlit as st
import requests
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from azure.monitor.opentelemetry.exporter import AzureMonitorTraceExporter
import os

# URL of your prediction API
website = "https://sentana006-f5dchbf0bacygude.francecentral-01.azurewebsites.net/predict"


# Initialize tracer only once using Streamlit session state
if not st.session_state.get("tracer_initialized") :
    # Initialize OpenTelemetry tracer provider
    trace.set_tracer_provider(TracerProvider())
    tracer = trace.get_tracer(__name__)

    # Set up the Azure Monitor Exporter
    exporter = AzureMonitorTraceExporter(
        connection_string="InstrumentationKey=" + str(os.environ["KEY001"])
    )
    
    # Add a span processor to export spans
    trace.get_tracer_provider().add_span_processor(BatchSpanProcessor(exporter))
    
    # Instrument requests library to automatically trace HTTP requests
    RequestsInstrumentor().instrument()
    
    # Mark tracer as initialized in session state
    st.session_state["tracer_initialized"] = True
else:
    tracer = trace.get_tracer(__name__)

# Streamlit front-end
st.title("What do you think about the new Deadpool movie?")

# Input text field
user_input = st.text_input("Enter your review", "")

# Analyze button
if st.button("Analyze"):
    if user_input:
        try:
            # Send the user input to the backend for prediction
            response = requests.post(website, json={"text": user_input})
            if response.status_code == 200:
                prediction = response.json().get("prediction")
                st.success(f"Prediction: {prediction}")
            else:
                st.error("Error: Status code != 200")
        except Exception as e:
            st.error(f"Error: {str(e)}")
    else:
        st.warning("Please enter your review")

# Messy answer button
if st.button("Click HERE if the answer is messy"):
    with tracer.start_as_current_span("manual_logging") as span:
        # span.set_attribute("button.clicked", True)
        # span.set_attribute("issue", "Response is not OK")
        span.add_event("User clicked messy answer button", {
            "Text sent": user_input
        })
        print("Span created for messy answer button click.")
    st.info("Issue has been logged. Thanks for your feedback!")

# Disclaimer
st.markdown(
    """
    <div style='font-size:0.85rem; color:#6c757d; text-align:center; background-color:#e9ecef; padding:10px; border-top:1px solid #dee2e6;'>
    By using this website, you consent to the collection of data from your computer, which will be utilized for educational purposes. The data will be processed through Azure Application Insights and temporarily stored.
    </div>
    """, unsafe_allow_html=True
)
