const PptxGenJS = require('pptxgenjs');
const path = require('path');

// Create presentation
const pptx = new PptxGenJS();

// Set metadata
pptx.author = 'Алмаз Сабитов';
pptx.company = 'Башкирэнерго';
pptx.subject = 'Описание заказчика';
pptx.title = 'О заказчике - Башкирэнерго';

// Add slide
const slide = pptx.addSlide();

// Background - dark navy for premium feel
slide.background = { color: '1E2761' };

// Title
slide.addText('О ЗАКАЗЧИКЕ', {
  x: 0.5,
  y: 0.4,
  w: 9,
  h: 0.8,
  fontSize: 36,
  fontFace: 'Arial Black',
  color: 'FFFFFF',
  bold: true,
  align: 'left',
  valign: 'middle'
});

// Accent line under title
slide.addShape(pptx.ShapeType.rect, {
  x: 0.5,
  y: 1.25,
  w: 2,
  h: 0.05,
  fill: { color: 'F96167' }
});

// Company name
slide.addText('ООО «БАШКИРЭНЕРГО»', {
  x: 0.5,
  y: 1.5,
  w: 9,
  h: 0.6,
  fontSize: 28,
  fontFace: 'Arial',
  color: 'F96167',
  bold: true,
  align: 'left',
  valign: 'middle'
});

// Subtitle
slide.addText('Производственное объединение информационных технологий и связи', {
  x: 0.5,
  y: 2.15,
  w: 9,
  h: 0.5,
  fontSize: 16,
  fontFace: 'Arial',
  color: 'CADCFC',
  italic: true,
  align: 'left',
  valign: 'middle'
});

// Description text
const description = `Компания «Башкирэнерго» — один из крупнейших энергетических холдингов России, обеспечивающий надежное электроснабжение Республики Башкортостан. 

ПО ИТиС (Производственное объединение информационных технологий и связи) отвечает за цифровую трансформацию и внедрение современных IT-решений в энергетической отрасли.`;

slide.addText(description, {
  x: 0.5,
  y: 2.9,
  w: 6,
  h: 2.2,
  fontSize: 14,
  fontFace: 'Arial',
  color: 'FFFFFF',
  align: 'left',
  valign: 'top',
  lineSpacing: 24,
  paraSpaceAfter: 12
});

// Key facts section
slide.addText('КЛЮЧЕВЫЕ ФАКТЫ', {
  x: 0.5,
  y: 5.3,
  w: 6,
  h: 0.4,
  fontSize: 16,
  fontFace: 'Arial Black',
  color: 'F96167',
  bold: true,
  align: 'left'
});

// Facts in columns
const facts = [
  { icon: '⚡', text: 'Энергетическая отрасль' },
  { icon: '🏢', text: 'Республика Башкортостан' },
  { icon: '👥', text: 'Тысячи клиентов' },
  { icon: '🔌', text: 'Технологическое присоединение' }
];

facts.forEach((fact, index) => {
  const col = index % 2;
  const row = Math.floor(index / 2);
  
  // Icon circle
  slide.addShape(pptx.ShapeType.ellipse, {
    x: 0.5 + col * 3.2,
    y: 5.8 + row * 0.7,
    w: 0.4,
    h: 0.4,
    fill: { color: 'F96167' }
  });
  
  // Icon text
  slide.addText(fact.icon, {
    x: 0.5 + col * 3.2,
    y: 5.8 + row * 0.7,
    w: 0.4,
    h: 0.4,
    fontSize: 16,
    color: 'FFFFFF',
    align: 'center',
    valign: 'middle'
  });
  
  // Fact text
  slide.addText(fact.text, {
    x: 1.0 + col * 3.2,
    y: 5.8 + row * 0.7,
    w: 2.5,
    h: 0.4,
    fontSize: 13,
    fontFace: 'Arial',
    color: 'FFFFFF',
    align: 'left',
    valign: 'middle'
  });
});

// Image placeholder - building photo
slide.addImage({
  path: 'C:\\Users\\almaz\\.qwen\\tmp\\clipboard\\clipboard-1776186950148-8567dad1-16f3-4cc0-8484-dca1276929ec.png',
  x: 7,
  y: 1.5,
  w: 5.5,
  h: 4.2,
  sizing: { type: 'contain', w: 5.5, h: 4.2 }
});

// Image caption
slide.addShape(pptx.ShapeType.rect, {
  x: 7,
  y: 5.8,
  w: 5.5,
  h: 0.6,
  fill: { color: 'CADCFC' },
  rectRadius: 0.1
});

slide.addText('Здание ПО ИТиС ООО «Башкирэнерго»', {
  x: 7,
  y: 5.8,
  w: 5.5,
  h: 0.6,
  fontSize: 12,
  fontFace: 'Arial',
  color: '1E2761',
  bold: true,
  align: 'center',
  valign: 'middle'
});

// Footer
slide.addShape(pptx.ShapeType.rect, {
  x: 0,
  y: 6.9,
  w: 13.33,
  h: 0.6,
  fill: { color: '0F1538' }
});

slide.addText('ИИ-ассистент по технологическому присоединению  •  2026', {
  x: 0.5,
  y: 6.95,
  w: 12.33,
  h: 0.5,
  fontSize: 11,
  fontFace: 'Arial',
  color: 'CADCFC',
  align: 'center',
  valign: 'middle'
});

// Save presentation
const outputPath = path.join(__dirname, '..', 'practice', 'О_заказчике_Башкирэнерго.pptx');
pptx.writeFile({ fileName: outputPath })
  .then(() => {
    console.log('✓ Презентация создана:', outputPath);
    process.exit(0);
  })
  .catch(err => {
    console.error('✗ Ошибка:', err);
    process.exit(1);
  });
