// scripts/convert-icons.js
const sharp = require('sharp');
const fs = require('fs');
const path = require('path');

const sizes = [72, 96, 128, 144, 152, 192, 384, 512];
const svgBuffer = fs.readFileSync('public/icon.svg');

async function convert() {
  // Cria pasta icons se não existir
  if (!fs.existsSync('public/icons')) {
    fs.mkdirSync('public/icons', { recursive: true });
  }
  
  for (const size of sizes) {
    await sharp(svgBuffer)
      .resize(size, size)
      .png()
      .toFile(`public/icons/icon-${size}x${size}.png`);
    console.log(`✅ Criado icon-${size}x${size}.png`);
  }
  
  // Copia apple-icon.png se existir
  if (fs.existsSync('public/apple-icon.png')) {
    fs.copyFileSync('public/apple-icon.png', 'public/icons/apple-icon.png');
  }
  
  console.log('✅ Todos os ícones foram criados!');
}

convert().catch(console.error);