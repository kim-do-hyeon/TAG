class Table_Info :
    def get_table_list(self) :
        return [table for table in self.info.keys()]
    
    def get_time_columns(self, table) :
        time_dict = self.time_column_dict
        if table in time_dict :
            return [date_col for date_col in time_dict[table].keys()]
    
    def get_info(self) :
        return self.info
    
    def get_time_dict(self) :
        return self.time_column_dict
    
    def __init__(self) :
        self.info = {
            "Chrome_Web_Visits" : {
                "type" : "web",
                "root_col_type" : "url",
                "root_col" : "URL",
                "time" : ["Date_Visited_Date/Time_-_UTC_(yyyy-mm-dd)"],
                "value_connection" : [
                    {
                        "type" : "url",
                        "col" : "url"
                    }
                ]
            },
            "Edge_Chromium_Web_Visits" : {
                "type" : "web",
                "root_col_type" : "url",
                "root_col" : "URL",
                "time" : ["Date_Visited_Date/Time_-_UTC_(yyyy-mm-dd)"],
                "value_connection" : [
                    {
                        "type" : "url",
                        "col" : "url"
                    }
                ]
            },
            "Jump_Lists" : {
                "type" : "file",
                "root_col_type" : "path",
                "root_col" : "Data",
                "value_connection" : [
                    {
                        "type" : "path",
                        "col" : "Data"
                    }
                ]
            },
            "PDF_Documents" : {
                "type" : "file",
                "root_col_type" : "name",
                "root_col" : "Filename",
                "value_connection" : [
                    {
                        "type" : "name",
                        "col" : "Filename"
                    }
                ]
            },
            "Text_Documents" : {
                "type" : "file",
                "root_col_type" : "name",
                "root_col" : "Filename",
                "value_connection" : [
                    {
                        "type" : "name",
                        "col" : "Filename"
                    }
                ]
            },
            "Microsoft_Excel_Documents" : {
                "type" : "file",
                "root_col_type" : "name",
                "root_col" : "Filename",
                "value_connection" : [
                    {
                        "type" : "name",
                        "col" : "Filename"
                    }
                ]
            },
            "Microsoft_PowerPoint_Documents" : {
                "type" : "file",
                "root_col_type" : "name",
                "root_col" : "Filename",
                "value_connection" : [
                    {
                        "type" : "name",
                        "col" : "Filename"
                    }
                ]
            },
            "Microsoft_Word_Documents" : {
                "type" : "file",
                "root_col_type" : "name",
                "root_col" : "Filename",
                "value_connection" : [
                    {
                        "type" : "name",
                        "col" : "Filename"
                    }
                ]
                
            },
            "Recycle_Bin" : {
                "type" : "file",
                "root_col_type" : "name",
                "root_col" : "File_Name",
                "value_connection" : [
                    {
                        "type" : "name",
                        "col" : "File_Name"
                    },
                    {
                        "type" : "path",
                        "col" : "Current_Location"
                    }
                ]
            },
            "MRU_Recent_Files_&_Folders" : {
                "type" : "file",
                "root_col_type" : "name",
                "root_col" : "File/Folder_Name",
                "value_connection" : [
                    {
                        "type" : "name",
                        "col" : "File/Folder_Name"
                    },
                    {
                        "type" : "name",
                        "col" : "File/Folder_Link"
                    }
                ]
            },
            "LNK_Files" : {
                "type" : "file",
                "root_col_type" : "path",
                "root_col" : "Linked_Path",
                "value_connection" : [
                    {
                        "type" : "path",
                        "col" : "Linked_Path"
                    }
                ]
            },
            "LogFile_Analysis" : {
                "type" : "file",
                "root_col_type" : "name",
                "root_col" :"File_Operation",
                "value_connection" : [
                    {
                        "type" : "name",
                        "col" : "Original_File_Name"
                    },
                    {
                        "type" : "name",
                        "col" : "Current_File_Name"
                    }
                ]
            },
            "Shellbags" : {
                "type" : "execute",
                "root_col_type" : "path",
                "root_col" : "Path"
            },
            "Chrome_Downloads" : {
                "type" : "web",
                "root_col_type" : "path",
                "root_col" : "Saved_To",
                "value_connection" : [
                    {
                        "type" : "path",
                        "col" : "Saved_To"
                    },
                    {
                        "type" : "url",
                        "col" : "Download_Source"
                    }
                ]
            },
            "Chrome_Logins" : {
                "type" : "web",
                "root_col_type" : "url",
                "root_col" : "URL",
                "value_connection" : [
                    {
                        "type" : "url",
                        "col" : "URL"
                    }
                ]
                
            },
            "Edge_Chromium_Downloads" : {
                "type" : "web",
                "root_col_type" : "url",
                "root_col" : "URL",
                "value_connection" : [
                    {
                        "type" : "path",
                        "col" : "Saved_To"
                    }
                ]
            },
            "Edge_Chromium_Logins" : {
                "type" : "web",
                "root_col_type" : "url",
                "root_col" : "URL",
                "value_connection" : [
                    {
                        "type" : "url",
                        "col" : "URL"
                    }
                ]
                
            },
            "Cloud_Services_URLs" : {
                "type" : "web",
                "root_col_type" : "url",
                "root_col" : "URL",
                "value_connection" : [
                    {
                        "type" : "url",
                        "col" : "URL"
                    }
                ]
            },
            # "USB_Devices" : {
            #     "type" : "usb",
            #     "root_col_type" : "serial_num",
            #     "root_col" : "Friendly_Name"
            # },
            "Prefetch_Files___Windows_8/10" : {
                "type" : "program",
                "root_col_type" : "program",
                "root_col" : "Application_Name"
            },
            "Shim_Cache" : {
                "type" : "program",
                "root_col_type" : "program",
                "root_col" : "File_Name"
            },
            "Windows_Event_Logs" : {
                "type" : "event",
                "root_col_type" : "event_id",
                "root_col" : "Model"
            },
            "Windows_Event_Logs___Storage_Device_Events" : {
                "type" : "event",
                "root_col_type" : "serial_num",
                "root_col" : "Model"
            }
        }
        
        self.time_column_dict = {
            "Edge_Chromium_Web_Visits" : {
                "Date_Visited_Date/Time_-_UTC_(yyyy-mm-dd)" : {
                    "type" : "web_visit"
                }
            },
            "Edge_Chromium_Downloads" : {
                "End_Time_Date/Time_-_UTC_(yyyy-mm-dd)" : {
                    "type" : "web_download_end",
                },
                "Start_Time_Date/Time_-_UTC_(yyyy-mm-dd)" : {
                    "type" : "web_download_start"
                }
            },
            "Edge_Chromium_Logins" : {
                "Created_Date/Time_-_UTC_(yyyy-mm-dd)" : {
                    "type" : "web_login"
                }
            },
            "Chrome_Web_Visits" : {
                "Date_Visited_Date/Time_-_UTC_(yyyy-mm-dd)" : {
                    "type" : "web_visit"
                }
            },
            "Chrome_Downloads" : {
                "End_Time_Date/Time_-_UTC_(yyyy-mm-dd)" : {
                    "type" : "web_download_end",
                },
                "Start_Time_Date/Time_-_UTC_(yyyy-mm-dd)" : {
                    "type" : "web_download_start"
                }
            },
            "Chrome_Logins" : {
                "Created_Date/Time_-_UTC_(yyyy-mm-dd)" : {
                    "type" : "web_login"
                }
            },
            "Cloud_Services_URLs" : {
                "Date/Time_-_UTC_(yyyy-mm-dd)" : {
                    "type" : "web_cloud"
                }
            },
            "Jump_Lists" : {
                "Target_File_Created_Date/Time_-_UTC_(yyyy-mm-dd)" : {
                    "target" : True,
                    "type" : "file_create"
                },
                "Target_File_Last_Modified_Date/Time_-_UTC_(yyyy-mm-dd)" : {
                    "target" : True,
                    "type" : "file_modify"
                },
                "Target_File_Last_Accessed_Date/Time_-_UTC_(yyyy-mm-dd)" : {
                    "target" : True,
                    "type" : "file_access"
                },
                "Last_Access_Date/Time_-_UTC_(yyyy-mm-dd)" : {
                    "type" : "jumplist_access"
                }
            },
            "LNK_Files" : {
                "Target_File_Last_Modified_Date/Time_-_UTC_(yyyy-mm-dd)" : {
                    "target" : True,
                    "type" : "file_modify"
                },
                "Target_File_Last_Accessed_Date/Time_-_UTC_(yyyy-mm-dd)" : {
                    "type" : "file_access",
                    "target" : True
                },
                "Target_File_Created_Date/Time_-_UTC_(yyyy-mm-dd)" : {
                    "target" : True,
                    "type" : "file_create"
                },
                "Last_Modified_Date/Time_-_UTC_(yyyy-mm-dd)" : {
                    "type" : "lnk_modify"
                },
                "Accessed_Date/Time_-_UTC_(yyyy-mm-dd)" : {
                    "type" : "lnk_access"
                },
                "Created_Date/Time_-_UTC_(yyyy-mm-dd)" : {
                    "type" : "lnk_create"
                }
            },
            # "USB_Devices" : {
            #     "Last_Insertion_Date/Time_-_UTC_(yyyy-mm-dd)" : {
            #         "type" : "usb_connect"
            #     },
            #     "First_Connected_Date/Time_-_Local_Time_(yyyy-mm-dd)" : {
            #         "type" : "usb_connect",
            #         "First" : True
            #     },
            #     "Last_Removal_Date/Time_-_UTC_(yyyy-mm-dd)" : {
            #         "type" : "usb_disconnect"
            #     },
            #     "Last_Connected_Date/Time_-_UTC_(yyyy-mm-dd)" : {
            #         "type" : "usb_connect"
            #     },
            #     "Install_Date/Time_-_UTC_(yyyy-mm-dd)" : {
            #         "type" : "usb_connect"
            #     },
            #     "First_Install_Date/Time_-_UTC_(yyyy-mm-dd)" : {
            #         "type" : "usb_connect",
            #         "First" : True
            #     }
            # },
            "Shellbags" : {
                "First_Interaction_Date/Time_-_UTC_(yyyy-mm-dd)" : {
                    "type" : "shellbag_interaction"
                },
                "System_Last_Modified_Date/Time_-_UTC_(yyyy-mm-dd)" : {
                    "type" : "shellbag_modify"
                },
                "File_System_Last_Accessed_Date/Time_-_UTC_(yyyy-mm-dd)" : {
                    "type" : "file_access",
                    "system" : True
                },
                "Last_Interaction_Date/Time_-_UTC_(yyyy-mm-dd)" : {
                    "type" : "shellbag_interaction"
                },
                "File_System_Created_Date/Time_-_UTC_(yyyy-mm-dd)" : {
                    "type" : "file_create",
                    "system" : True
                }
            },
            "PDF_Documents" : {
                "File_System_Created_Date/Time_-_UTC_(yyyy-mm-dd)" : {
                    "type" : "file_create",
                    "system" : True
                },
                "File_System_Last_Modified_Date/Time_-_UTC_(yyyy-mm-dd)" : {
                    "type" : "file_modify",
                    "system" : True
                },
                "Last_Interaction_Date/Time_-_UTC_(yyyy-mm-dd)" : {
                    "type" : "file_modify",
                },
                "File_System_Last_Accessed_Date/Time_-_UTC_(yyyy-mm-dd)" : {
                    "type" : "file_access",
                    "system" : True
                },
                "Created_Date/Time_-_UTC_(yyyy-mm-dd)" : {
                    "type" : "file_create"
                },
                "Last_Modified_Date/Time_-_UTC_(yyyy-mm-dd)" : {
                    "type" : "file_modify"
                }
            },
            "Text_Documents" : {
                "Last_Accessed_Date/Time_-_UTC_(yyyy-mm-dd)" : {
                    "type" : "file_access"
                },
                "Created_Date/Time_-_UTC_(yyyy-mm-dd)" : {
                    "type" : "file_create"
                },
                "Last_Modified_Date/Time_-_UTC_(yyyy-mm-dd)" : {
                    "type" : "file_modify"
                }
            },
            "Microsoft_Excel_Documents" : {
                "File_System_Created_Date/Time_-_UTC_(yyyy-mm-dd)" : {
                    "type" : "file_create",
                    "system" : True
                },
                "File_System_Last_Modified_Date/Time_-_UTC_(yyyy-mm-dd)" : {
                    "type" : "file_modify",
                    "system" : True
                },
                "File_System_Last_Accessed_Date/Time_-_UTC_(yyyy-mm-dd)" : {
                    "type" : "file_access",
                    "system" : True
                },
                "Created_Date/Time_-_UTC_(yyyy-mm-dd)" : {
                    "type" : "file_create"
                },
                "Last_Modified_Date/Time_-_UTC_(yyyy-mm-dd)" : {
                    "type" : "file_modify"
                },
                "Last_Printed_Date/Time_-_UTC_(yyyy-mm-dd)" : {
                    "type" : "print"
                }
            },
            "Microsoft_PowerPoint_Documents" : {
                "File_System_Created_Date/Time_-_UTC_(yyyy-mm-dd)" : {
                    "type" : "file_create",
                    "system" : True
                },
                "File_System_Last_Modified_Date/Time_-_UTC_(yyyy-mm-dd)" : {
                    "type" : "file_modify",
                    "system" : True
                },
                "File_System_Last_Accessed_Date/Time_-_UTC_(yyyy-mm-dd)" : {
                    "type" : "file_access",
                    "system" : True
                },
                "Created_Date/Time_-_UTC_(yyyy-mm-dd)" : {
                    "type" : "file_create"
                },
                "Last_Modified_Date/Time_-_UTC_(yyyy-mm-dd)" : {
                    "type" : "file_modify"
                }
            },
            "Microsoft_Word_Documents" : {
                "File_System_Created_Date/Time_-_UTC_(yyyy-mm-dd)" : {
                    "type" : "file_create",
                    "system" : True
                },
                "File_System_Last_Modified_Date/Time_-_UTC_(yyyy-mm-dd)" : {
                    "type" : "file_modify",
                    "system" : True
                },
                "File_System_Last_Accessed_Date/Time_-_UTC_(yyyy-mm-dd)" : {
                    "type" : "file_access",
                    "system" : True
                },
                "Created_Date/Time_-_UTC_(yyyy-mm-dd)" : {
                    "type" : "file_create"
                },
                "Last_Modified_Date/Time_-_UTC_(yyyy-mm-dd)" : {
                    "type" : "file_modify"
                },
                "Last_Printed_Date/Time_-_UTC_(yyyy-mm-dd)" : {
                    "type" : "print"
                }
            },
            "Prefetch_Files___Windows_8/10" : {
                "include" : {
                    "what" : "Run",
                    "type" : "program_run",
                },
                "File_Created_Date/Time_-_UTC_(yyyy-mm-dd)" : {
                    "type" : "program_run"
                }
            },
            "Shim_Cache" : {
                "Last_Updated_Date/Time_-_UTC(yyyy-mm-dd)" : {
                    "type" : "program_run",
                }
            },
            "Recycle_Bin" : {
                "Deleted_Date/Time_-_UTC_(yyyy-mm-dd)" : {
                    "type" : "file_delete"
                }
            },
            "MRU_Recent_Files_&_Folders" : {
                "Registry_Key_Modified_Date/Time_-_UTC_(yyyy-mm-dd)" : {
                    "type" : "file_access"
                }
            },
            "Windows_Event_Logs___Storage_Device_Events" : {
                "Created_Date/Time_-_UTC_(yyyy-mm-dd)" : {
                    "type" : {
                        "Action" : {
                            "Connected" : "usb_connect",
                            "Disconnected" : "usb_disconnect"
                        }
                    }
                }
            }
            # "Windows_Event_Logs" : {
            #     "Created_Date/Time_-_UTC_(yyyy-mm-dd)" : {
            #         "type" : "windows_event_log"
            #     }
            # },
        }
        
table_info_class = Table_Info()

print(table_info_class.get_table_list())