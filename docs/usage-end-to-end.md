# How to run end-to-end tests

To setup your development environment, see [How to setup a development environment](docs/usage-development.md)

# Run end-to-end tests

Start an interactive Kubernetes deployment of 2 nodes:

```
# Start the deployment
sudo make -C enjoliver-testsuite check_euid_it_plans_enjolivage_disk_2_nodes
```


## Tips
Connect inside with `ssh`:

`./enjoliver-testsuite/s.sh`
