import { readFileSync } from 'node:fs';
import { validateDeliveryRegister } from '../lib/alberta-delivery.mjs';
const file =
  process.argv[2] || 'data/governance/alberta-delivery-register.json';
validateDeliveryRegister(JSON.parse(readFileSync(file, 'utf8')));
console.log('Delivery register passed evidence and integrity checks.');
