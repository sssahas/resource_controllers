run-local:
	python app.py

docker-build:
	podman build -t localhost/api_controller:latest .

docker-run:
	podman run -p 8080:8080 -e AWS_ACCESS_KEY_ID={{your_key}} -e AWS_SECRET_ACCESS_KEY={{your_secret}} -e AWS_DEFAULT_REGION={{your_region}} localhost/api_controller:latest