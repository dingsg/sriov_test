#!/usr/bin/expect  
set username [lindex $argv 0]  
set password [lindex $argv 1]  
set hostname [lindex $argv 2]
set home [lindex $argv 3]  
if {[file isfile $home/.ssh/id_rsa]!=1} {
    spawn ssh-keygen -t rsa
    expect {
	"Enter file in which to save the key*" {
	    send "\r"
	    expect {
		"Enter passphrase*" {
		    send "\r"
		    expect "Enter same passphrase again*"
		    send "\r"
		}
		"Overwrite (y/n)?" {
		    send "n\r"
		}
	    }
	}
    }
    expect eof
}
spawn ssh-copy-id -f -i $home/.ssh/id_rsa.pub $username@$hostname
expect {
    #first connect, no public key in ~/.ssh/known_hosts
    "Are you sure you want to continue connecting*" {
	send "yes\r"
	expect "password:"
	send "$password\r"
    }
    #already has public key in ~/.ssh/known_hosts
    "password:" {
	send "$password\r"
    }
    "Now try logging into the machine" {
	#it has authorized, do nothing!
    }
}
expect eof
