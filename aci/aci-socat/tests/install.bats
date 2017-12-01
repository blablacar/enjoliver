#!/dgr/bin/bats

@test "is well installed" {
  [ -f /usr/bin/socat ]
}

@test "is able to run" {
  run /usr/bin/socat -V
  [ "$status" -eq 0 ]
}
