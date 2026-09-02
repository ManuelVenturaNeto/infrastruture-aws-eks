#!/usr/bin/env bash
set -euo pipefail

install -d /opt/proxy

cat > /opt/proxy/connect-proxy.py <<'PYTHON'
${proxy}
PYTHON

cat > /etc/systemd/system/connect-proxy.service <<'UNIT'
[Unit]
Description=Proxy CONNECT para a API do EKS
After=network-online.target
Wants=network-online.target

[Service]
ExecStart=/usr/bin/python3 /opt/proxy/connect-proxy.py 127.0.0.1 ${porta}
Restart=always
RestartSec=5
DynamicUser=yes
NoNewPrivileges=yes
ProtectSystem=strict
ProtectHome=yes
PrivateTmp=yes

[Install]
WantedBy=multi-user.target
UNIT

systemctl daemon-reload
systemctl enable --now connect-proxy.service
