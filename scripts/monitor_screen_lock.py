import subprocess
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Literal

# python3 -m pip install -U fastapi==0.121.0 email-validator>2.0
app = FastAPI(title="Screen Lock Monitor", version="1.0.0")

"""
A FastAPI application to monitor screen lock status using xscreensaver-command.

cp -rv ./install/* ~/.config/
systemctl --user daemon-reload

systemctl --user enable monitor_screen_locked.service

systemctl --user start monitor_screen_locked.service

journalctl --user -u monitor_screen_locked.service -f
"""


class ScreenStatus(BaseModel):
    status: Literal["locked", "blank", "unlocked"]
    raw_output: str


@app.get("/screen-status", response_model=ScreenStatus)
async def get_screen_status():
    """
    Check if the screen is locked, blank, or unlocked using xscreensaver-command.

    Returns:
        ScreenStatus: Object containing the screen status and raw output
    """
    try:
        result = subprocess.run(
            ["xscreensaver-command", "-time"],
            capture_output=True,
            text=True,
            check=True
        )
        output = result.stdout.strip().lower()

        # Determine status based on xscreensaver output
        # Check for non-blanked first to avoid matching "blank" in "non-blanked"
        if "screen non-blanked" in output or "screen saver off" in output:
            status = "unlocked"
        elif "screen locked" in output or "locked" in output:
            status = "locked"
        elif "screen blanked" in output or "blank since" in output:
            status = "blank"
        else:
            # Default to unlocked if we can't determine
            status = "unlocked"

        return ScreenStatus(status=status, raw_output=output)

    except subprocess.CalledProcessError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute xscreensaver-command: {e.stderr}"
        )
    except FileNotFoundError:
        raise HTTPException(
            status_code=500,
            detail="xscreensaver-command not found. Please ensure xscreensaver is installed."
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error: {str(e)}"
        )


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Screen Lock Monitor API",
        "endpoints": {
            "/screen-status": "GET - Check current screen lock status",
            "/docs": "GET - Interactive API documentation"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app,
        # host="0.0.0.0",
        host="127.0.0.1",
        port=8000,
        log_level="warning",
        access_log=False,
    )
