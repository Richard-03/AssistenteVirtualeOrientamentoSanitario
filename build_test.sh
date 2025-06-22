#!/bin/bash
docker compose stop backend_service frontend_service
docker compose up --build backend_service frontend_service