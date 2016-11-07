package main

import (
	"testing"
	"net/http"
	"time"
	"io/ioutil"
	"encoding/json"
)

func TestPostToDiscovery(t *testing.T) {
	var data DiscoveryData

	//var interfaces []Iface
	i := Iface{
		IPv4:"192.168.1.1",
		CIDRv4:"192.168.1.1/24",
		Netmask:24,
		Name:"eth0",
		MAC:"00:00:00:00:00",
	}
	data.Interfaces = append(data.Interfaces, i)

	//var bootInfo BootInfo
	data.BootInfo.Mac = "00-00-00-00-00"
	data.BootInfo.Uuid = "2023e709-39b4-47d7-8905-e8be3e6bc2c6"

	//data.BootInfo = bootInfo

	CONF.DiscoveryAddress = "http://127.0.0.1:8080"
	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		var bodyBytes []byte
		bodyBytes, _ = ioutil.ReadAll(r.Body)
		var rcvData DiscoveryData

		err := json.Unmarshal(bodyBytes, &rcvData)
		if err != nil {
			t.Error(err)
		}
	})
	go func() {
		e := http.ListenAndServe("127.0.0.1:8080", nil)
		if e != nil {
			t.Log(e)
			t.Fail()
		}
	}()
	var err error
	// wait or not the http server go routine
	for i := 0; i < 10; i++ {
		err := PostToDiscovery(data)
		if err == nil {
			break
		} else {
			t.Log(err)
			time.Sleep(100 * time.Millisecond)
		}
	}
	if err != nil {
		t.Log(err)
		t.Fail()
	}
}

