from fastapi import FastAPI, HTTPException, Request
import requests
from fastapi.openapi.utils import get_openapi

KEY_SERVER_URL = "http://127.0.0.1:8000"

app = FastAPI(title="Service Server", docs_url="/docs")

# Validate key with service name
def validate_key_for_service(key: str, service: str):
    try:
        response = requests.get(f"{KEY_SERVER_URL}/keys/validate/{key}")
        if response.status_code != 200:
            return False

        key_data = response.json()
        return service.upper() in [s.upper() for s in key_data.get("services", [])]

    except Exception as e:
        print("🔴 Error contacting key server:", e)
        return False

# Service endpoints
@app.get("/service_a")
def service_a(request: Request):
    key = request.headers.get("authorization")
    if not validate_key_for_service(key, "A"):
        raise HTTPException(status_code=403, detail="Not authorized for Service A")
    return {"message": "✅ Welcome to Service A"}

@app.get("/service_b")
def service_b(request: Request):
    key = request.headers.get("authorization")
    if not validate_key_for_service(key, "B"):
        raise HTTPException(status_code=403, detail="Not authorized for Service B")
    return {"message": "✅ Welcome to Service B"}

@app.get("/service_c")
def service_c(request: Request):
    key = request.headers.get("authorization")
    if not validate_key_for_service(key, "C"):
        raise HTTPException(status_code=403, detail="Not authorized for Service C")
    return {"message": "✅ Welcome to Service C"}

@app.get("/service_d")
def service_d(request: Request):
    key = request.headers.get("authorization")
    if not validate_key_for_service(key, "D"):
        raise HTTPException(status_code=403, detail="Not authorized for Service D")
    return {"message": "✅ Welcome to Service D"}

@app.get("/service_e")
def service_e(request: Request):
    key = request.headers.get("authorization")
    if not validate_key_for_service(key, "E"):
        raise HTTPException(status_code=403, detail="Not authorized for Service E")
    return {"message": "✅ Welcome to Service E"}

# Swagger Authorize button
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    schema = get_openapi(
        title="Service Server",
        version="1.0.0",
        description="Service routes protected by API key.",
        routes=app.routes,
    )

    schema.setdefault("components", {})["securitySchemes"] = {
        "APIKeyHeader": {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization"
        }
    }

    for path in schema["paths"].values():
        for operation in path.values():
            operation["security"] = [{"APIKeyHeader": []}]

    app.openapi_schema = schema
    return app.openapi_schema

app.openapi = custom_openapi
