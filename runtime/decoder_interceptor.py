"""
Intercept Decoder to extract player roster from game packets
"""
import decoderx

# Store player data
player_roster = {}  # {player_id: {'data': ..., 'secret': False}}
num_players_detected = 0
_decoder_inspected = False  # Only inspect once

# Get original methods
_original_set_num_players = decoderx.Decoder.set_num_players

def intercept_set_num_players(self, num):
    """Intercept set_num_players method"""
    global num_players_detected, player_roster, _decoder_inspected
    
    # Call original method FIRST to let it process
    result = _original_set_num_players(self, num)
    
    try:
        # ONE-TIME: Inspect decoder attributes to see what's available
        if not _decoder_inspected:
            _decoder_inspected = True
            attrs = [a for a in dir(self) if not a.startswith('_')]
            print(f"[CUEADD-DECODER] Available attributes: {attrs}")
            # Try to find player data with IPs
            for attr in attrs:
                try:
                    val = getattr(self, attr)
                    if val is not None and not callable(val):
                        print(f"[CUEADD-DECODER]   {attr} = {val}")
                except:
                    pass
        # After processing, check the decoder instance's state
        # Try to find num_players attribute on the decoder instance
        if hasattr(self, 'num_players'):
            current_num = self.num_players
            if isinstance(current_num, int) and current_num != num_players_detected:
                num_players_detected = current_num
                print(f"[CUEADD-DECODER] ✓ Detected {num_players_detected} players from decoder.num_players")
                
                # Create player roster
                if num_players_detected > 0:
                    player_roster.clear()
                    for i in range(min(num_players_detected, 6)):
                        player_id = f"P{i+1}"
                        player_roster[player_id] = {
                            'data': None,
                            'secret': False
                        }
                    print(f"[CUEADD-DECODER] Created roster: P1-P{min(num_players_detected, 6)}")
        
        # Also try other common attribute names
        for attr in ['player_count', 'players', '_num_players']:
            if hasattr(self, attr):
                val = getattr(self, attr)
                if isinstance(val, int) and val > 0 and val != num_players_detected:
                    num_players_detected = val
                    print(f"[CUEADD-DECODER] ✓ Found {num_players_detected} players from decoder.{attr}")
                    break
                    
    except Exception as e:
        # Silently ignore - gets called frequently
        pass
    
    return result

# Monkey patch the Decoder class
print("[CUEADD-DECODER] Installing decoder interceptors...")
decoderx.Decoder.set_num_players = intercept_set_num_players
print("[CUEADD-DECODER] ✓ Decoder interceptors installed")

def get_player_roster():
    """Get current player roster"""
    return dict(player_roster)

def get_num_players():
    """Get number of players detected"""
    return num_players_detected
