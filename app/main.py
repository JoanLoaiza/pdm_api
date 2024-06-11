from fastapi import FastAPI, WebSocket, Depends
from sqlalchemy.orm import Session
from app.database import engine, Base, get_db
from app.models import DataSensor
from app.crud import save_data, get_all_data
from starlette.websockets import WebSocketDisconnect
import json
from decimal import Decimal

app = FastAPI()

Base.metadata.create_all(bind=engine)

active_connections = []

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, db: Session = Depends(get_db)):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            saved_data = save_data(db, data)
            response_data = {
                "id_sensor": saved_data.id_sensor,
                "id_locacion": saved_data.id_locacion,
                "fecha": saved_data.fecha.isoformat(),
                "eje_x": float(saved_data.eje_x) if isinstance(saved_data.eje_x, Decimal) else saved_data.eje_x,
                "eje_y": float(saved_data.eje_y) if isinstance(saved_data.eje_y, Decimal) else saved_data.eje_y,
                "eje_z": float(saved_data.eje_z) if isinstance(saved_data.eje_z, Decimal) else saved_data.eje_z
            }
            for connection in active_connections:
                await connection.send_json(response_data)
    except WebSocketDisconnect:
        active_connections.remove(websocket)
        print("WebSocket connection closed.")

@app.get("/data")
def get_data(db: Session = Depends(get_db)):
    data = get_all_data(db)
    return data

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="http://servo.ucp.edu.co", port=8000)
