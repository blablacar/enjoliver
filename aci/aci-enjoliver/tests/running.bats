#!/dgr/bin/bats

@test "Tests are OK" {
  make -C /go/src/github.com/blablacar/enjoliver/enjoliver-testsuite testing.id_rsa
  make -C /go/src/github.com/blablacar/enjoliver/enjoliver-testsuite check
  [ $? -eq 0 ]
}

@test "Default config" {
  /go/src/github.com/blablacar/enjoliver/manage.py show-configs
  [ $? -eq 0 ]
}
