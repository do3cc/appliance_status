run: build
	docker run -it --rm \
        -v ${PWD}/config.json:/usr/src/app/config.json:ro \
        -v /run/systemd/netif/leases/:/usr/src/app/leases:ro \
        -v ${PWD}/appliance_status_py/examples/tests.json:/usr/src/app/tests.json:ro \
        -v ${PWD}/appliance_status_py/examples/schema.json:/usr/src/app/schema.json:ro \
        --network="host" \
		do3cc/appliance_status

build:
	docker build -t do3cc/appliance_status .

push: build
	docker push do3cc/appliance_status:latest

test:
	cd appliance_status_py && make test && cd ../appliance_status_js && yarn && yarn && yarn test
