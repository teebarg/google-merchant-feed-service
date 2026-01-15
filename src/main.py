from fastapi import FastAPI, HTTPException
from src.sync import sync_products
from src.scheduler import start_scheduler
from dotenv import load_dotenv
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    load_dotenv()
    start_scheduler()
    yield


app = FastAPI(title="Google Merchant Feed Service", lifespan=lifespan)


@app.get("/sync")
def run_sync():
    try:
        result = sync_products()
        return {"status": "ok", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def health():
    return {"status": "ok"}

# from fastapi import FastAPI
# from src.sync import sync_products
# from src.scheduler import start_scheduler
# from dotenv import load_dotenv
# from contextlib import asynccontextmanager
# import os

# # OpenTelemetry
# from opentelemetry import trace
# from opentelemetry.sdk.trace import TracerProvider
# from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor
# from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

# # Setup tracing
# trace.set_tracer_provider(TracerProvider())
# tracer = trace.get_tracer(__name__)
# span_processor = SimpleSpanProcessor(ConsoleSpanExporter())
# trace.get_tracer_provider().add_span_processor(span_processor)

# load_dotenv()

# print("OpenTelemetry initialized")
# print(os)

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     start_scheduler()
#     yield

# app = FastAPI(title="Google Merchant Feed Service", lifespan=lifespan)
# FastAPIInstrumentor.instrument_app(app)

# @app.post("/sync")
# def run_sync():
#     with tracer.start_as_current_span("sync-products-endpoint"):
#         result = sync_products()
#         return {"status": "ok", "result": result}
