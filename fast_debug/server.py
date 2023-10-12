import bdb
import json
import threading

import jsonpickle
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()


def generate_cmd_from_import_path(import_path: str) -> str:
    module_name, func_name = import_path.rsplit(".", 1)
    return f"""
import importlib
module = importlib.import_module('{module_name}')
getattr(module, '{func_name}')()
"""


class DebuggerState:
    def __init__(self):
        self.debugger = None
        self.event = threading.Event()
        self.current_frame = None
        self.classpath = None

    def stop_debugging(self):
        if not self.debugger:
            print("Debugger is not initialized")
            return

        self.debugger.set_quit()
        self.debugger = None
        self.current_frame = None
        self.event.set()
        print("Debugging stopped and state reset")

    def start(self):
        if not self.debugger:
            print("Debugger is not initialized")
            return
        print("Starting debugger: ", self.classpath)

        cmd = generate_cmd_from_import_path(self.classpath)
        threading.Thread(target=self.debugger.run, args=(cmd,)).start()


debugger_state = DebuggerState()


class MyWebDebug(bdb.Bdb):
    def user_line(self, frame):
        debugger_state.current_frame = frame
        debugger_state.event.clear()  # Pause execution until an action is given via the API
        debugger_state.event.wait()


class InitRequest(BaseModel):
    classpath: str


@app.post("/debug/init")
def init_debugger(request: InitRequest):
    debugger_state.classpath = request.classpath
    debugger_state.stop_debugging()
    debugger_state.debugger = MyWebDebug()
    print("Debugger initialized")


@app.get("/debug/stop")
def stop_debugging():
    debugger_state.stop_debugging()
    return


class BreakpointRequest(BaseModel):
    filepath: str
    line: int


@app.post("/debug/set_breakpoint")
def set_breakpoint(request: BreakpointRequest):
    if not debugger_state.debugger:
        raise HTTPException(status_code=400, detail="Debugger is not initialized")

    debugger_state.debugger.set_break(request.filepath, request.line)
    return {
        "status": "Breakpoint set",
        "filepath": request.filepath,
        "line": request.line,
    }


@app.get("/debug/start")
def start_debugging():
    if not debugger_state.debugger:
        raise HTTPException(status_code=400, detail="Debugger is not initialized")

    debugger_state.start()
    return {"status": "Debugging started"}


@app.get("/debug/step")
def step():
    if debugger_state.current_frame:
        debugger_state.event.set()  # Resume execution until next line
        return {"status": "Stepped to next line"}
    else:
        raise HTTPException(status_code=400, detail="Debugger is not paused")


@app.get("/debug/vars")
def get_vars():
    if debugger_state.current_frame:
        local_vars = debugger_state.current_frame.f_locals

        vars_serialized = jsonpickle.encode(debugger_state.current_frame.f_locals)
        print(f"frame: {debugger_state.current_frame}")
        print("Local variables:", local_vars)
        return json.loads(vars_serialized)
    else:
        raise HTTPException(status_code=400, detail="Debugger is not paused")


def run():
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8002)


if __name__ == "__main__":
    run()
