@echo off
REM Check if container exists
docker ps -a -q -f name=my_redis_dev > temp_container.txt
set /p containerId=<temp_container.txt
del temp_container.txt

if "%containerId%"=="" (
    REM Container does not exist, create & run it
    echo Creating and starting Redis container...
    docker run -d --name my_redis_dev -p 6379:6379 redis
) else (
    REM Container exists, check if running
    docker ps -q -f name=my_redis_dev > temp_running.txt
    set /p runningId=<temp_running.txt
    del temp_running.txt

    if "%runningId%"=="" (
        REM Container exists but stopped - start it
        echo Starting existing Redis container...
        docker start my_redis_dev
    ) else (
        echo Redis container is already running.
    )
)

REM Start FastAPI server in a new terminal window
start cmd /k uvicorn main:app --reload
