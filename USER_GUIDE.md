# Bender - User Guide

## Introduction
Welcome to **Bender**, your shiny metal Linux workstation dashboard! Designed for GNOME (GTK4 + libadwaita), Bender wraps common daily Linux sysadmin tasks into a polished, tabbed GUI. No more remembering obscure bash commands—Bender has you covered!

## Features and Tabs
Bender provides a unified interface divided into several specialized tabs:

### 1. System Overview
Get a quick glance at your machine's vital statistics. Monitor CPU usage, RAM consumption, and overall system load in real time. 

### 2. Security Audit
Ensure your system is hardened and safe. Run security audits, verify firewall status, and review security policies seamlessly without digging through terminal logs. This tab leverages our ShadowAgent Rules to keep your data secure.

### 3. Network Monitor & Connections
Keep track of your network interfaces, active connections, and traffic. Whether you are debugging a connectivity issue or just monitoring bandwidth, this tab offers real-time insights.

### 4. Maintenance
Keep your system clean and running efficiently. Easily clear caches, manage systemd services, and remove orphaned packages with a single click.

### 5. Weather
Check the local forecast right from your dashboard. Bender integrates with `ansiweather` to bring you accurate, terminal-styled weather reports wrapped in a beautiful UI.

### 6. Proxy Manager
Seamlessly configure and switch between proxy settings. Ideal for developers and sysadmins working across different corporate networks or VPNs.

## Security & Architecture
Bender is engineered with security first. We have recently implemented **Security Hardening updates (B-01 to B-06)**, which close shell injection vectors, replace vulnerable XML parsers, and enforce strict download size guards.

Enjoy using Bender, and remember to check for updates regularly!
