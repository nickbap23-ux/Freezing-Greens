"""
Monkey patch divertx.Divert to intercept packets globally
This hooks into the GUI's WinDivert instance
"""
import divertx
import socket

# Store detected player IPs globally
detected_players = set()  # All WinDivert users detected
all_ips_seen = set()
packet_count = 0
local_ips = set()  # YOUR IPs (safe list)
target_v1_ips = set()  # OTHER v1 users to target (detected_players - local_ips)

# NEW: Enhanced player tracking
all_players = {}  # {ip: {'packets': count, 'is_cheater': bool, 'first_seen': packet_num}}
other_players = set()  # All other players (not you, not server)
cheaters = set()  # V1 & V2 users (WinDivert detected)
legit_players = set()  # Legit players (no cheats detected)

# Defense Mode state
defense_mode_active = False
defense_target_ip = None  # Court IP
defense_packets_sent = 0
defense_divert_handle = None  # Store divert handle for packet injection

# Per-Player Lag Mode
lagging_players = set()  # IPs of players we're actively lagging
lag_packets_dropped = {}  # {ip: count}

# Original recv method
_original_recv = divertx.Divert.recv

def is_court_server(ip):
    """Check if IP is a court server"""
    return (ip.startswith('3.') or ip.startswith('18.') or 
            ip.startswith('34.') or ip.startswith('52.') or
            ip.startswith('54.') or ip.startswith('10.') or 
            ip.startswith('172.'))

def intercepted_recv(self):
    """Intercept packets from GUI's WinDivert"""
    global packet_count, defense_mode_active, defense_target_ip, defense_packets_sent, defense_divert_handle
    global local_ips, target_v1_ips, lagging_players, lag_packets_dropped
    global all_players, other_players, cheaters, legit_players
    
    # Store divert handle for Defense Mode to use
    if defense_mode_active and defense_divert_handle is None:
        defense_divert_handle = self
    
    # Call original recv
    result = _original_recv(self)
    
    if result and result is not None:
        try:
            packet, addr = result
            if packet is None or addr is None:
                return result
            
            packet_count += 1
            
            # Parse IP header from ALL packets
            if len(packet) >= 20:
                ip_header = packet[:20]
                src_ip = socket.inet_ntoa(ip_header[12:16])
                dst_ip = socket.inet_ntoa(ip_header[16:20])
                
                # Log ALL unique IPs seen
                for ip in [src_ip, dst_ip]:
                    if ip not in all_ips_seen:
                        all_ips_seen.add(ip)
                        print(f"[CUEADD] New IP seen: {ip}")
                
                # Check for WinDivert injections
                is_injection = self.is_second_hop(packet)
                
                # Track ALL players with enhanced detection
                for ip in [src_ip, dst_ip]:
                    if ip not in all_players:
                        all_players[ip] = {
                            'packets': 0,
                            'is_cheater': False,
                            'first_seen': packet_count
                        }
                    
                    all_players[ip]['packets'] += 1
                    
                    # Mark as cheater if WinDivert injection detected
                    if is_injection:
                        all_players[ip]['is_cheater'] = True
                
                if packet_count <= 10:  # First 10 packets for debug
                    print(f"[CUEADD] Packet #{packet_count}: {src_ip}->{dst_ip}, is_second_hop={is_injection}")
                
                # Identify LOCAL IPs (your own IPs - first 30 packets)
                if packet_count <= 30:
                    if not is_court_server(dst_ip):
                        if src_ip not in local_ips and not is_court_server(src_ip):
                            local_ips.add(src_ip)
                            print(f"[CUEADD] ✓ LOCAL IP (you): {src_ip}")
                    
                    # Identify court server
                    if is_court_server(dst_ip) and defense_target_ip is None:
                        defense_target_ip = dst_ip
                        print(f"[CUEADD] ✓ COURT SERVER: {dst_ip}")
                
                # Analyze players at packet 50
                if packet_count == 50:
                    print("\n" + "="*60)
                    print("[CUEADD-DETECT] ANALYZING PLAYERS...")
                    print("="*60)
                    
                    for ip, info in all_players.items():
                        # Skip your IPs
                        if ip in local_ips:
                            continue
                        
                        # Skip court server
                        if ip == defense_target_ip or is_court_server(ip):
                            continue
                        
                        # This is another player!
                        if info['packets'] >= 5:
                            if ip not in other_players:
                                other_players.add(ip)
                                
                                # Categorize: Cheater or Legit
                                if info['is_cheater']:
                                    cheaters.add(ip)
                                    target_v1_ips.add(ip)
                                    detected_players.add(ip)
                                    badge = "🔴 V1 & V2 USER"
                                else:
                                    legit_players.add(ip)
                                    badge = "✅ LEGIT PLAYER"
                                
                                print(f"[CUEADD-DETECT] ⚡ PLAYER: {ip} ({info['packets']} pkts) - {badge}")
                    
                    print("="*60)
                    print(f"[CUEADD-DETECT] ✅ Players found:")
                    print(f"[CUEADD-DETECT]   🔴 V1 & V2: {len(cheaters)}")
                    print(f"[CUEADD-DETECT]   ✅ Legit: {len(legit_players)}")
                    print(f"[CUEADD-DETECT]   Total: {len(other_players)}")
                    print("="*60 + "\n")
                
                # Continuous detection (after packet 50)
                if packet_count > 50:
                    for ip in [src_ip, dst_ip]:
                        if (ip not in other_players and 
                            ip not in local_ips and
                            ip != defense_target_ip and
                            not is_court_server(ip)):
                            
                            info = all_players[ip]
                            if info['packets'] >= 10:
                                other_players.add(ip)
                                
                                if info['is_cheater']:
                                    cheaters.add(ip)
                                    target_v1_ips.add(ip)
                                    detected_players.add(ip)
                                    badge = "🔴 V1 & V2"
                                else:
                                    legit_players.add(ip)
                                    badge = "✅ Legit"
                                
                                print(f"[CUEADD-DETECT] ⚡ NEW PLAYER: {ip} - {badge}")
                    
                    # Update cheater status if detected later
                    if is_injection:
                        for ip in [src_ip, dst_ip]:
                            if ip in other_players:
                                if not all_players[ip]['is_cheater']:
                                    # Newly detected as cheater!
                                    all_players[ip]['is_cheater'] = True
                                    if ip in legit_players:
                                        legit_players.remove(ip)
                                    cheaters.add(ip)
                                    target_v1_ips.add(ip)
                                    detected_players.add(ip)
                                    print(f"[CUEADD-DETECT] ⚠️  {ip} is using V1 & V2!")
                
                # PER-PLAYER LAG MODE: Drop packets from specific players we're lagging
                if lagging_players:
                    # Check if this packet is FROM a lagging player
                    if src_ip in lagging_players:
                        import random
                        # Drop 90% of their packets to make them lag
                        if random.random() < 0.90:
                            if src_ip not in lag_packets_dropped:
                                lag_packets_dropped[src_ip] = 0
                            lag_packets_dropped[src_ip] += 1
                            
                            if lag_packets_dropped[src_ip] % 50 == 0:
                                print(f"[CUEADD-LAG] Dropped {lag_packets_dropped[src_ip]} packets FROM {src_ip}")
                            
                            # Block this packet - player will lag
                            return (None, None)
                
                # DEFENSE MODE: Block ALL traffic involving v1 users
                # If on same local network (hotspot), we can intercept their packets
                if defense_mode_active:
                    # Block packets FROM v1 users OR TO v1 users
                    if src_ip in target_v1_ips or dst_ip in target_v1_ips:
                        try:
                            import random
                            # Aggressive blocking - 95% drop rate
                            if random.random() < 0.95:
                                defense_packets_sent += 1
                                
                                if defense_packets_sent % 100 == 0:
                                    direction = "FROM" if src_ip in target_v1_ips else "TO"
                                    target = src_ip if src_ip in target_v1_ips else dst_ip
                                    print(f"[CUEADD-DEFENSE] Blocked {defense_packets_sent} packets {direction} {target}")
                                
                                # DON'T pass this packet through - completely block it
                                # On same local network, this prevents their game from working
                                # Leading to lag/timeout for everyone
                                return (None, None)
                        except Exception as e:
                            pass
        except Exception as e:
            # Don't break the GUI's packet processing
            print(f"[CUEADD] Error: {e}")
    
    # Always return the original result
    return result

# Monkey patch!
divertx.Divert.recv = intercepted_recv
print("[CUEADD] ✓ Monkey patched Divert.recv()")

def get_detected_players():
    """Get list of WinDivert user IPs (Secret v1)"""
    return list(detected_players)

def get_all_ips():
    """Get ALL unique IPs seen in traffic"""
    return list(all_ips_seen)

def is_secret_user(ip):
    """Check if IP is using WinDivert (Secret v1)"""
    return ip in detected_players

def get_local_ips():
    """Get YOUR local IPs (safe list)"""
    return list(local_ips)

def get_target_v1_ips():
    """Get OTHER v1 user IPs to target"""
    return list(target_v1_ips)

def enable_defense_mode(target_ip):
    """Enable Defense Mode - inject attack packets to overwhelm server"""
    global defense_mode_active, defense_target_ip, defense_packets_sent, defense_divert_handle
    defense_mode_active = True
    defense_target_ip = target_ip
    defense_packets_sent = 0
    defense_divert_handle = None
    print(f"[CUEADD-DEFENSE] Defense Mode ENABLED - injecting attack packets to {target_ip}")

def disable_defense_mode():
    """Disable Defense Mode"""
    global defense_mode_active, defense_target_ip, defense_packets_sent, defense_divert_handle
    print(f"[CUEADD-DEFENSE] Defense Mode DISABLED - injected {defense_packets_sent} total attack packets")
    defense_mode_active = False
    defense_target_ip = None
    defense_packets_sent = 0
    defense_divert_handle = None

def enable_player_lag(player_ip):
    """Start lagging a specific player by dropping their packets"""
    global lagging_players, lag_packets_dropped
    if player_ip and player_ip not in lagging_players:
        lagging_players.add(player_ip)
        lag_packets_dropped[player_ip] = 0
        print(f"[CUEADD-LAG] ⚡ Started lagging player: {player_ip}")
        return True
    return False

def disable_player_lag(player_ip):
    """Stop lagging a specific player"""
    global lagging_players, lag_packets_dropped
    if player_ip in lagging_players:
        lagging_players.remove(player_ip)
        count = lag_packets_dropped.get(player_ip, 0)
        print(f"[CUEADD-LAG] ✓ Stopped lagging {player_ip} - dropped {count} packets")
        return True
    return False

def get_lagging_players():
    """Get list of players currently being lagged"""
    return list(lagging_players)

def get_cheaters():
    """Get V1 & V2 cheater IPs"""
    return list(cheaters)

def get_legit_players():
    """Get legit player IPs (no cheats detected)"""
    return list(legit_players)

def get_other_players():
    """Get all other player IPs (cheaters + legit)"""
    return list(other_players)

def get_player_info(ip):
    """Get info about a specific player"""
    return all_players.get(ip, None)
