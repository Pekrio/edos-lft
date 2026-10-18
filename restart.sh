# 1. Stop and remove all running Docker containers
docker rm -f $(docker ps -aq) 2>/dev/null || true

# 2. Clean up dangling network namespace links
sudo rm -rf /var/run/netns/*

# 3. Clean up orphaned Open vSwitch bridges on the host
sudo ovs-vsctl list-br | xargs -r -n 1 sudo ovs-vsctl del-br

# 4. Flush dangling iptables NAT rules
sudo iptables -t nat -F

# 5. Prune unused Docker network bridges
docker network prune -f
sleep 2
sudo reboot
