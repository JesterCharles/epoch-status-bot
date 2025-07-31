import sqlite3
from typing import Optional, List, Tuple

class Database:
    def __init__(self, db_file: str):
        self.db_file = db_file
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS guild_settings (
                guild_id INTEGER PRIMARY KEY,
                channel_id INTEGER NOT NULL,
                gambling_channel_id INTEGER
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notification_optins (
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                user_name TEXT,
                PRIMARY KEY (guild_id, user_id)
            )
        ''')
        try:
            cursor.execute('ALTER TABLE notification_optins ADD COLUMN user_name TEXT')
        except sqlite3.OperationalError:
            pass
        
        # Add gambling_channel_id column if it doesn't exist
        try:
            cursor.execute('ALTER TABLE guild_settings ADD COLUMN gambling_channel_id INTEGER')
        except sqlite3.OperationalError:
            pass
        
        # Gambling tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gambling_balances (
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                balance INTEGER NOT NULL DEFAULT 100,
                last_daily_claim INTEGER DEFAULT 0,
                PRIMARY KEY (guild_id, user_id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gambling_bets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                user_name TEXT,
                bet_amount INTEGER NOT NULL,
                predicted_time TEXT NOT NULL,
                predicted_timestamp INTEGER NOT NULL,
                placed_at INTEGER NOT NULL,
                betting_day TEXT NOT NULL,
                is_active INTEGER DEFAULT 1
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS gambling_jackpots (
                guild_id INTEGER PRIMARY KEY,
                current_pot INTEGER DEFAULT 0,
                multiplier INTEGER DEFAULT 1,
                last_reset_day TEXT NOT NULL
            )
        ''')
        
        # Add new columns to existing tables if they don't exist
        try:
            cursor.execute('ALTER TABLE gambling_balances ADD COLUMN last_daily_claim INTEGER DEFAULT 0')
        except sqlite3.OperationalError:
            pass
        
        try:
            cursor.execute('ALTER TABLE gambling_bets ADD COLUMN betting_day TEXT NOT NULL DEFAULT ""')
        except sqlite3.OperationalError:
            pass
        
        conn.commit()
        conn.close()

    def set_notification_channel(self, guild_id: int, channel_id: int):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO guild_settings (guild_id, channel_id) VALUES (?, ?)",
            (guild_id, channel_id)
        )
        conn.commit()
        conn.close()

    def get_notification_channel(self, guild_id: int) -> Optional[int]:
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT channel_id FROM guild_settings WHERE guild_id = ?", (guild_id,))
        result = cursor.fetchone()
        conn.close()
        if result:
            return result[0]
        return None

    def add_optin_user(self, guild_id: int, user_id: int, user_name: Optional[str] = None):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO notification_optins (guild_id, user_id, user_name) VALUES (?, ?, ?)",
            (guild_id, user_id, user_name)
        )
        conn.commit()
        conn.close()

    def remove_optin_user(self, guild_id: int, user_id: int):
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM notification_optins WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id)
        )
        conn.commit()
        conn.close()

    def get_optin_users(self, guild_id: int) -> List[Tuple[int, Optional[str]]]:
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT user_id, user_name FROM notification_optins WHERE guild_id = ?",
            (guild_id,)
        )
        users = [(row[0], row[1]) for row in cursor.fetchall()]
        conn.close()
        return users

    # --- Gambling System Methods ---
    
    def get_gambling_balance(self, guild_id: int, user_id: int, starting_balance: int = 100) -> int:
        """Get user's current epoch balance."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT balance FROM gambling_balances WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id)
        )
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return result[0]
        else:
            # First time user, give them starting balance
            self.set_gambling_balance(guild_id, user_id, starting_balance)
            return starting_balance

    def set_gambling_balance(self, guild_id: int, user_id: int, balance: int):
        """Set user's epoch balance."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO gambling_balances (guild_id, user_id, balance) VALUES (?, ?, ?)",
            (guild_id, user_id, balance)
        )
        conn.commit()
        conn.close()

    def add_gambling_bet(self, guild_id: int, user_id: int, user_name: str, bet_amount: int, 
                        predicted_time: str, predicted_timestamp: int, placed_at: int, betting_day: str) -> bool:
        """Add a new bet to the database."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO gambling_bets 
                (guild_id, user_id, user_name, bet_amount, predicted_time, predicted_timestamp, placed_at, betting_day)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (guild_id, user_id, user_name, bet_amount, predicted_time, predicted_timestamp, placed_at, betting_day))
            conn.commit()
            return True
        except Exception as e:
            print(f"Error adding bet: {e}")
            return False
        finally:
            conn.close()

    def get_active_gambling_bets(self, guild_id: int) -> List[Tuple]:
        """Get all active bets for a guild."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT user_name, bet_amount, predicted_time, predicted_timestamp
            FROM gambling_bets 
            WHERE guild_id = ? AND is_active = 1
            ORDER BY predicted_timestamp ASC
        ''', (guild_id,))
        results = cursor.fetchall()
        conn.close()
        return results

    def claim_daily_epochs(self, guild_id: int, user_id: int, current_day: str, daily_amount: int = 50) -> Tuple[bool, str]:
        """Claim daily epochs if user hasn't claimed today and has placed at least one bet.
        Returns (success, reason)"""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        try:
            # Check if user has ever placed a bet
            cursor.execute('''
                SELECT COUNT(*) FROM gambling_bets 
                WHERE guild_id = ? AND user_id = ?
            ''', (guild_id, user_id))
            bet_count = cursor.fetchone()[0]
            
            if bet_count == 0:
                return False, "no_bets"
            
            # Get current balance and last claim day
            cursor.execute('''
                SELECT balance, last_daily_claim FROM gambling_balances 
                WHERE guild_id = ? AND user_id = ?
            ''', (guild_id, user_id))
            result = cursor.fetchone()
            
            if result:
                current_balance, last_claim = result
                if last_claim == current_day:
                    return False, "already_claimed"
                
                # Update balance and claim day
                cursor.execute('''
                    UPDATE gambling_balances 
                    SET balance = balance + ?, last_daily_claim = ?
                    WHERE guild_id = ? AND user_id = ?
                ''', (daily_amount, current_day, guild_id, user_id))
            else:
                # First time user, create record with daily claim
                cursor.execute('''
                    INSERT INTO gambling_balances (guild_id, user_id, balance, last_daily_claim)
                    VALUES (?, ?, ?, ?)
                ''', (guild_id, user_id, 100 + daily_amount, current_day))
            
            conn.commit()
            return True, "success"
        except Exception as e:
            print(f"Error claiming daily epochs: {e}")
            return False, "error"
        finally:
            conn.close()

    def has_claimed_daily(self, guild_id: int, user_id: int, current_day: str) -> bool:
        """Check if user has already claimed daily epochs today."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT last_daily_claim FROM gambling_balances 
            WHERE guild_id = ? AND user_id = ?
        ''', (guild_id, user_id))
        result = cursor.fetchone()
        conn.close()
        
        if result and result[0] == current_day:
            return True
        return False

    def has_placed_any_bet(self, guild_id: int, user_id: int) -> bool:
        """Check if user has ever placed a bet."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) FROM gambling_bets 
            WHERE guild_id = ? AND user_id = ?
        ''', (guild_id, user_id))
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0

    def get_current_jackpot(self, guild_id: int) -> Tuple[int, int]:
        """Get current jackpot amount and multiplier."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT current_pot, multiplier FROM gambling_jackpots 
            WHERE guild_id = ?
        ''', (guild_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return result[0], result[1]
        return 0, 1

    def update_jackpot(self, guild_id: int, additional_pot: int, current_day: str):
        """Add to the current jackpot."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO gambling_jackpots (guild_id, current_pot, multiplier, last_reset_day)
            VALUES (?, 
                    COALESCE((SELECT current_pot FROM gambling_jackpots WHERE guild_id = ?), 0) + ?,
                    COALESCE((SELECT multiplier FROM gambling_jackpots WHERE guild_id = ?), 1),
                    ?)
        ''', (guild_id, guild_id, additional_pot, guild_id, current_day))
        conn.commit()
        conn.close()

    def rollover_jackpot(self, guild_id: int, current_day: str):
        """Double the jackpot for rollover to next day."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE gambling_jackpots 
            SET current_pot = current_pot * 2, multiplier = multiplier * 2, last_reset_day = ?
            WHERE guild_id = ?
        ''', (current_day, guild_id))
        
        # If no jackpot exists, create one
        if cursor.rowcount == 0:
            cursor.execute('''
                INSERT INTO gambling_jackpots (guild_id, current_pot, multiplier, last_reset_day)
                VALUES (?, 0, 2, ?)
            ''', (guild_id, current_day))
        
        conn.commit()
        conn.close()

    def reset_daily_bets(self, guild_id: int, current_day: str):
        """Mark all bets from previous days as inactive."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE gambling_bets 
            SET is_active = 0 
            WHERE guild_id = ? AND betting_day != ? AND is_active = 1
        ''', (guild_id, current_day))
        conn.commit()
        conn.close()

    def get_active_gambling_bets_for_day(self, guild_id: int, betting_day: str) -> List[Tuple]:
        """Get all active bets for a specific day."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT user_name, bet_amount, predicted_time, predicted_timestamp
            FROM gambling_bets 
            WHERE guild_id = ? AND betting_day = ? AND is_active = 1
            ORDER BY predicted_timestamp ASC
        ''', (guild_id, betting_day))
        results = cursor.fetchall()
        conn.close()
        return results

    def set_gambling_channel(self, guild_id: int, channel_id: int):
        """Set the gambling channel for a guild."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        
        # Check if guild settings exist
        cursor.execute("SELECT gambling_channel_id FROM guild_settings WHERE guild_id = ?", (guild_id,))
        result = cursor.fetchone()
        
        if result is not None:
            # Update existing record
            cursor.execute(
                "UPDATE guild_settings SET gambling_channel_id = ? WHERE guild_id = ?",
                (channel_id, guild_id)
            )
        else:
            # Insert new record (we need a notification channel_id, so we'll use the gambling channel as default)
            cursor.execute(
                "INSERT INTO guild_settings (guild_id, channel_id, gambling_channel_id) VALUES (?, ?, ?)",
                (guild_id, channel_id, channel_id)
            )
        
        conn.commit()
        conn.close()

    def get_gambling_channel(self, guild_id: int) -> Optional[int]:
        """Get the gambling channel for a guild."""
        conn = sqlite3.connect(self.db_file)
        cursor = conn.cursor()
        cursor.execute("SELECT gambling_channel_id FROM guild_settings WHERE guild_id = ?", (guild_id,))
        result = cursor.fetchone()
        conn.close()
        if result:
            return result[0]
        return None
