## How to setup a development environment

This part will soon have a better documentation.

If you still want to try you can follow this steps:

## Requirements:

* **Linux** with filesystem overlay for `dgr`
* See `apt.sh` for the needed packages or `sudo make apt`
* See `.travis.yml` as a setup example & unit / integration tests

## Setup
All in one dev setup:

    # Clone the project inside a valid GOPATH
    git clone https://github.com/blablacar/enjoliver.git ${GOPATH}/src/github.com/blablacar/enjoliver

    # Be sure the GOPATH is fowarded across Makefiles or do it step by step
    sudo -E make dev_setup

Step-by-step:

    make submodules
    make -C runtime dev_setup
    make -C enjoliver-testsuite testing.id_rsa
    make front
    make -C matchbox/assets/discoveryC
    make -C matchbox/assets/enjoliver-agent

    # Very long:
    sudo -E make aci
    sudo -E make container_linux

    # misc
    make config
    sudo -E chown -R ${SUDO_USER}: $(CWD)

    # Validate
    make validate

The enjoliver API is available on `127.0.0.1:5000`, the user interface is behind the `/ui`


## Access to the kubernetes cluster
At the end of the setup, a kubectl proxy is running on `127.0.0.1:8001`


    Starting to serve on 127.0.0.1:8001
    #####################################
    mkdir -pv ~/.kube
    cat << EOF >> ~/.kube/config
    apiVersion: v1
    clusters:
    - cluster:
        server: http://127.0.0.1:8001
      name: enjoliver
    contexts:
    - context:
        cluster: enjoliver
        namespace: default
        user:
      name: e
    current-context: e
    kind: Config
    preferences:
      colors: true
    EOF
    kubectl config use-context e
    #####################################


