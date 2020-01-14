#!/usr/bin/env python
import os
import time
import sys

cloud_name = sys.argv[1]
compute_node = sys.argv[2]
aggregate_name = sys.argv[3]

def aggregate_check():
  aggr_list = os.popen("openstack --os-cloud {} aggregate list -c Name | tail -n+4 | head -n-1 | awk '{{print $2}}'".format(cloud_name)).read().strip()
  print(aggr_list)
  var1 = os.popen("openstack --os-cloud {} hypervisor show {} | grep -i aggregate | awk '{{print $4}}'".format(cloud_name, compute_node)).read()
  print(var1) 
  if aggregate_name in var1:
     print("Compute node is already in correct aggregate.")
  else:
     print("Adding compute node to correct aggregate")
     print(os.popen("openstack --os-cloud {} aggregate add host {} {}".format(cloud_name, aggregate_name, compute_node)).read())

def boot_instance():
  if "zephyr" in cloud_name:
    netid = "int_network"
    image = "Cirros"
    flavor = "m1.tiny"

  elif "cloud05" in cloud_name:
    netid = "inner-net2"
    image = "CirrOS"
    flavor = "IaaS.Vcpu_2.ram_1.hdd_1"   

  print(netid)
  print(image)
  
  jenkins_vm = (os.popen('openstack --os-cloud {} server list -c Name -f value | grep test-jenkins-2'.format(cloud_name)).read()).strip()
  if jenkins_vm != "test-jenkins-2":
     availability_zone=os.popen('openstack --os-cloud {} aggregate show {} -f yaml | grep availability_zone | cut -d ":" -f2'.format(cloud_name, aggregate_name)).read().strip() 
     os.popen("openstack --os-cloud {} server create --image {} --flavor {} --availability-zone {}:{} --nic net-id={} test-jenkins-2 --wait".format(cloud_name, image, flavor, availability_zone, compute_node, netid)).read()
     #var3 = os.popen("openstack --os-cloud {} server create --image {} --flavor {} --availability-zone {}:{} --nic net-id={} test-jenkins-2 --wait".format(cloud_name, image, flavor, availability_zone, compute_node, netid)).read()
     print(os.popen('openstack --os-cloud {} server show test-jenkins-2'.format(cloud_name)).read()) 
     time.sleep(10)
     floating_ip = os.popen('openstack --os-cloud {} floating ip list -c "Floating IP Address" -c Port | grep None | tail -1 | awk "{{print $2}}" | cut -d "|" -f2'.format(cloud_name)).read().strip()
     os.popen("openstack --os-cloud {} server add floating ip test-jenkins-2 {}".format(cloud_name, floating_ip)).read()
     time.sleep(20)
     pckt1 = os.popen('ping -c4 {} | grep "packet loss" | cut -d "," -f3 | awk "{{print $1}}" | awk "{{print $1}}"'.format(floating_ip)).read()
     if "0%" in pckt1:
       print("Ping works correctly....................................")
       for i in range(10):
         print(i*".")
       #var6 = os.popen('openstack --os-cloud {} aggregate show {} -f yaml | grep netcracker.com | grep -v {} | cut -d " " -f2 | head -n 1'.format(cloud_name, aggregate_name, compute_node)).read().strip()
       aggr_hosts = os.popen('openstack --os-cloud {} aggregate show {} -f yaml | grep netcracker.com | grep -v {} | cut -d " " -f2'.format(cloud_name, aggregate_name, compute_node)).read().split()
       for host in aggr_hosts:
       #print(os.popen('openstack --os-cloud {} server migrate --live {} test-jenkins-2 --wait'.format(cloud_name, var6)).read())
         print(os.popen('openstack --os-cloud {} server migrate --live {} test-jenkins-2 --wait'.format(cloud_name, host)).read())
       #print(os.popen('openstack --os-cloud {} server show test-jenkins-2'.format(cloud_name)).read())
         hyp_name = os.popen('openstack --os-cloud {} server show test-jenkins-2 -f yaml | grep hypervisor_hostname | cut -d ":" -f3'.format(cloud_name)).read().strip()
         if hyp_name != compute_node:
           print(os.popen('openstack --os-cloud {} server show test-jenkins-2'.format(cloud_name)).read())
           print("VM is successfully migrated")
           break
         else:
           print("continue migrating VM")
       pckt2 = os.popen('ping -c4 {} | grep "packet loss" | cut -d "," -f3 | awk "{{print $1}}" | awk "{{print $1}}"'.format(floating_ip)).read()
       if "0%" in pckt2:
         print("Ping works correctly post migration to {} .....................................".format(hyp_name))
         print(os.popen('openstack --os-cloud {} server migrate --live {} test-jenkins-2 --wait'.format(cloud_name, compute_node)).read())
         print(os.popen('openstack --os-cloud {} server show test-jenkins-2'.format(cloud_name)).read())
         pckt3 = os.popen('ping -c4 {} | grep "packet loss" | cut -d "," -f3 | awk "{{print $1}}" | awk "{{print $1}}"'.format(floating_ip)).read()
         if "0%" in pckt3:
           print("Ping works correctly post migration to original hypervisor {}  ....................................".format(compute_node))
         else:
           print("Ping doesn't work xxxxxxxxxxxxxxxxxxxxxxx")
           sys.exit(9)
       else:
         print("Ping doesn't work   xxxxxxxxxxxxxxxxxxxxxxxxx")
         sys.exit(9)
     else:
       print("Ping doesn't work xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
       sys.exit(9)
  else:
    print("There is already an existing VM with name 'test-jenkins-2'") 
    sys.exit(9)

def main():
  aggregate_check()
  boot_instance()
#print(os.popen('openstack --os-cloud {} server delete test-jenkins-2 --wait'.format(cloud_name)).read())
#print("VM 'test-jenkins-2' has been deleted")

if __name__ == '__main__':
     main() 
