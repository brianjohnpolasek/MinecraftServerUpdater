import os
import requests
import time
import hashlib

# CONSTANTS
MINECRAFT_URL = "https://launchermeta.mojang.com/mc/game/version_manifest.json"
SHUTDOWN_DELAY_TIME = 5

def main():
	curr_sha = getCurrentSha()
	json_data = getJsonData()
	if checkForUpdate(curr_sha, json_data):
		updateServer(json_data)
		print ("DONE")

def getJsonData():
	print("Getting JSON data...")
	release_data = requests.get(MINECRAFT_URL).json()
	
	print ("Latest release: " + release_data['latest']['release'])
	
	for version in release_data['versions']:
		if version['id'] == '1.16.4':
			json_data = requests.get(version['url']).json()
			break
	
	print ("Obtained JSON data")
	return json_data

def getCurrentSha():
	print("Getting Sha of server...")
	server_jar = open("server.jar", 'rb')
	sha = hashlib.sha1()
	sha.update(server_jar.read())
	print("Server Sha found")
	return sha.hexdigest()

def checkForUpdate(curr_sha, json_data):
	print ("Checking for updates...")
	online_sha = json_data['downloads']['server']['sha1']
	
	if online_sha == '':
		print ("Update Required!")
		return True
	else:
		print ("No Update Needed!")
		return False

def updateServer(json_data):
	print ("Updating server...")
	# Download new server jar file
	server_jar_url = requests.get(json_data['downloads']['server']['url'])
	open('temp.jar', 'wb').write(server_jar_url.content)

	if checkTmuxStatus():
		shutdownServer()
	else:
		createTmuxSession()
	
	current_release = json_data['id']

	backupWorld(current_release)

	replaceServerJar(current_release)

	restartServer()
	
	print ("Server updated")

def checkTmuxStatus():
	print ("Checking Tmux status...")
	os.system('touch temp.txt')
	os.system('tmux list-sessions > temp.txt')
	
	temp_file = open('temp.txt', 'r')

	for line in temp_file:
		if "Minecraft" in line:
			print ("Tmux running")
			os.system('rm temp.txt')
			return True

	print ("Tmux not running")
	os.system('rm temp.txt')
	return False	

def shutdownServer():
	print ("Shutting down server in " + SHUTDOWN_DELAY_TIME + " seconds...")
	os.system('tmux send-keys -t Minecraft.0 "/say SYSTEM SHUTDOWN IN 1 MINUTE" ENTER')
	time.sleep(SHUTDOWN_DELAY_TIME)
	os.system('tmux send-keys -t Minecraft.0 "/stop" ENTER')
	print ("Server shutdown")

def createTmuxSession():
	print("Creating new Tmux session...")
	os.system('tmux new -d -s Minecraft')
	print ("Tmux session created")

def backupWorld(release):
	print ("Backing up world...")
	if os.path.exists('world_backups') == False:
		os.system('mkdir world_backups')

	tar_world_command = 'tar -czvf world_backups/world_' + release + ' world'
	os.system(tar_world_command)
	print ("Backup created")

def replaceServerJar(release):
	print ("replacing old server.jar...")
	if os.path.exists("jar_backups") == False:
		os.system('mkdir jar_backups')		

	move_old_server_command = 'mv server.jar jar_backups/server_' + release + '.jar'
	os.system(move_old_server_command)

	os.system('mv temp.jar server.jar')
	print ("Old server.jar replaced")

def restartServer():
	print ("Restarting server...")
	os.system('tmux send-keys -t Minecraft.0 "java -Xmx1024M -Xms1024M -jar server.jar nogui" ENTER')
	print ("Server restarted")


if __name__ == '__main__':
	main()
