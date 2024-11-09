const fs = require('fs');
const path = require('path');
const readline = require('readline');

const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
});

// Configuration
const GAME_NAME = 'WomanCommunication';
const CREATOR_NAME = 'GameCreatorNeko';
const BASE_SAVE_PATH = path.join(process.env.USERPROFILE, 'AppData', 'LocalLow', CREATOR_NAME, GAME_NAME);

// Utility functions
function ensureDirectoryExists(dirPath) {
    if (!fs.existsSync(dirPath)) {
        fs.mkdirSync(dirPath, { recursive: true });
    }
}

function copyDirectory(src, dest) {
    ensureDirectoryExists(dest);
    const entries = fs.readdirSync(src, { withFileTypes: true });

    for (const entry of entries) {
        const srcPath = path.join(src, entry.name);
        const destPath = path.join(dest, entry.name);

        if (entry.isDirectory()) {
            copyDirectory(srcPath, destPath);
        } else {
            fs.copyFileSync(srcPath, destPath);
        }
    }
}

function clearDirectory(dirPath) {
    if (fs.existsSync(dirPath)) {
        const entries = fs.readdirSync(dirPath, { withFileTypes: true });
        for (const entry of entries) {
            const fullPath = path.join(dirPath, entry.name);
            if (entry.isDirectory()) {
                fs.rmSync(fullPath, { recursive: true, force: true });
            } else {
                fs.unlinkSync(fullPath);
            }
        }
    }
}

// Main functions
async function replaceCheckpoint() {
    const checkpointsDir = path.join(__dirname, 'checkpoints');
    const checkpoints = fs.readdirSync(checkpointsDir);

    console.log('\nAvailable checkpoints:');
    checkpoints.forEach((cp, index) => {
        console.log(`${index + 1}. ${cp}`);
    });

    const answer = await new Promise(resolve => {
        rl.question('\nSelect checkpoint number to restore: ', resolve);
    });

    const selectedIndex = parseInt(answer) - 1;
    if (selectedIndex >= 0 && selectedIndex < checkpoints.length) {
        const selectedCheckpoint = path.join(checkpointsDir, checkpoints[selectedIndex]);
        console.log(`Replacing savedata with checkpoint: ${checkpoints[selectedIndex]}`);
        
        clearDirectory(BASE_SAVE_PATH);
        copyDirectory(selectedCheckpoint, BASE_SAVE_PATH);
        
        console.log('Checkpoint restored successfully!');
    } else {
        console.log('Invalid selection!');
    }
}

async function backupSavedata() {
    const currentDate = new Date().toISOString().replace(/[:.]/g, '-');
    const backupPath = `${BASE_SAVE_PATH}-${currentDate}`;
    
    console.log(`Creating backup at: ${backupPath}`);
    copyDirectory(BASE_SAVE_PATH, backupPath);
    console.log('Backup created successfully!');
}

async function recoverSavedata() {
    const userProfile = process.env.USERPROFILE;
    const localLowPath = path.join(userProfile, 'AppData', 'LocalLow');
    const backupDirs = fs.readdirSync(localLowPath)
        .filter(dir => dir.startsWith(`${CREATOR_NAME}\\${GAME_NAME}-`))
        .map(dir => path.join(localLowPath, dir));

    if (backupDirs.length === 0) {
        console.log('No backups found!');
        return;
    }

    console.log('\nAvailable backups:');
    backupDirs.forEach((dir, index) => {
        const dirName = path.basename(dir);
        console.log(`${index + 1}. ${dirName}`);
    });

    const answer = await new Promise(resolve => {
        rl.question('\nSelect backup number to restore: ', resolve);
    });

    const selectedIndex = parseInt(answer) - 1;
    if (selectedIndex >= 0 && selectedIndex < backupDirs.length) {
        console.log(`Restoring backup: ${path.basename(backupDirs[selectedIndex])}`);
        
        clearDirectory(BASE_SAVE_PATH);
        copyDirectory(backupDirs[selectedIndex], BASE_SAVE_PATH);
        
        console.log('Backup restored successfully!');
    } else {
        console.log('Invalid selection!');
    }
}

// Main menu
async function showMenu() {
    while (true) {
        console.log('\n=== Game Savedata Manager ===');
        console.log('1. Replace with checkpoint');
        console.log('2. Backup current savedata');
        console.log('3. Recover from backup');
        console.log('4. Exit');

        const answer = await new Promise(resolve => {
            rl.question('\nSelect an option: ', resolve);
        });

        switch (answer) {
            case '1':
                await replaceCheckpoint();
                break;
            case '2':
                await backupSavedata();
                break;
            case '3':
                await recoverSavedata();
                break;
            case '4':
                console.log('Goodbye!');
                rl.close();
                return;
            default:
                console.log('Invalid option!');
        }
    }
}

// Start the program
ensureDirectoryExists(BASE_SAVE_PATH);
showMenu();