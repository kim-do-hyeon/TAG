
class Windows_Event_Log :
    
    def is_windows_event_log(self, event_id) :
        return (self.get_windows_event_log_type(event_id=event_id) is not None)
    
    def get_windows_event_log_type(self, event_id) :
        for key, ids in self.event_id_dict.items() :
            if event_id in ids.keys() :
                return key, ids[event_id]
        return None, None
    
    def get_id_list(self) :
        id_list = []
        for category, events in self.event_id_dict.items():
            id_list.extend(events.keys())
        return id_list
    
    def __init__(self) :
        self.event_id_dict = {
            "logon_logout_authentication": {
                "4624": "Successful logon",
                "4625": "Failed logon attempt",
                "4634": "Logoff event",
                "4647": "User initiated logoff",
                "4672": "Special privileges assigned at logon",
                "4776": "NTLM authentication attempt",
                "4768": "Kerberos TGT request",
                "4769": "Kerberos service ticket request",
                "4771": "Kerberos pre-authentication failed",
                "4627": "Local system account logon"
            },
            "account_management": {
                "4720": "User account created",
                "4722": "User account enabled",
                "4725": "User account disabled",
                "4726": "User account deleted",
                "4738": "User account changed",
                "4740": "User account locked out",
                "4765": "SID history added",
                "4766": "SID history add failed"
            },
            "file_access_and_leakage": {
                "4663": "File or directory access attempt",
                "4656": "Handle opened for an object",
                "4660": "File deleted",
                "4657": "Object deleted or modified"
            },
            "external_device_and_usb": {
                "6416": "External device connected",
                "4663": "File access on external device",
                "4723": "Password change attempt on external device",
                "4724": "Password reset attempt",
                "1102": "Event log cleared"
            },
            "network_access_and_connection": {
                "4624": "Remote logon success",
                "4625": "Remote logon failure",
                "5140": "Network share object accessed",
                "5156": "Windows Firewall allowed connection",
                "5157": "Windows Firewall blocked connection"
            },
            "printer_usage": {
                "307": "Print job success",
                "805": "Printer driver installed",
                "310": "Print job failed"
            },
            "system_events": {
                "6005": "Event log service started",
                "6006": "Event log service stopped",
                "6013": "System uptime",
                "1100": "System shutdown",
                "104": "Windows service start attempt"
            },
            "process_creation_and_termination": {
                "4688": "New process created",
                "4689": "Process terminated",
                "4697": "Service installation",
                "4698": "Scheduled task created",
                "4699": "Scheduled task deleted"
            },
            "registry_activity": {
                "4657": "Registry value modified",
                "4662": "Access to an object in registry",
                "4985": "Registry policy loaded",
                "5038": "Security setting modified"
            },
            "suspicious_activity_detection": {
                "4688": "Suspicious process creation",
                "4720": "Unexpected account creation",
                "1102": "Event log deletion",
                "7035": "Service started or stopped",
                "7040": "Service start type changed",
                "7036": "Service status changed"
            },
            "windows_defender_and_security": {
                "1116": "Malware detected and action taken",
                "1117": "Malware removal failed",
                "5007": "Windows Defender settings modified",
                "5011": "Real-time protection disabled"
            },
            "group_policy_and_security_changes": {
                "4719": "Audit policy changed",
                "4902": "Audit subcategory changed",
                "4950": "Windows Firewall settings modified",
                "4904": "Integrity policy changed",
                "4905": "IPsec policy not applied"
            }
        }