const bancos = [
  { id: 1, nombre: "1 AV Villas" },
  { id: 2, nombre: "2 Banagrario" },
  { id: 3, nombre: "3 Bancamía" },
  { id: 4, nombre: "4 Banco Corficolombia (Panamá) S.A." },
  { id: 5, nombre: "5 Banco Corficolombiana (Panamá) S.A." },
  { id: 6, nombre: "6 Banco Davivienda" },
  { id: 7, nombre: "7 Banco Davivienda (Panamá) S.A." },
  { id: 8, nombre: "8 Banco Davivienda S.A. Miami International Bank Branch" },
  { id: 9, nombre: "9 Banco de Bogotá" },
  { id: 10, nombre: "10 Banco de Bogotá - Miami Agency" },
  { id: 11, nombre: "11 Banco de Bogotá - New York Agency" },
  { id: 12, nombre: "12 Banco de Bogotá (Panamá) S.A." },
  { id: 13, nombre: "13 Banco de Crédito del Perú - BCP -" },
  { id: 14, nombre: "14 Banco de la República" },
  { id: 15, nombre: "15 Banco de Occidente" },
  { id: 16, nombre: "16 Banco de Occidente (Panamá)" },
  { id: 17, nombre: "17 Banco Falabella" },
  { id: 18, nombre: "18 Banco GNB Sudameris" },
  { id: 19, nombre: "19 Banco Pichincha" },
  { id: 20, nombre: "20 Banco Popular" },
  { id: 21, nombre: "21 Banco Santander" },
  { id: 22, nombre: "22 Bancolombia Banca de Inversión" },
  { id: 23, nombre: "23 Colpatria Cayman Inc." },
  { id: 24, nombre: "24 Bancolombia" },
  { id: 25, nombre: "25 Bancolombia (Panamá) S.A." },
  { id: 26, nombre: "26 Bancolombia Miami Agency" },
  { id: 27, nombre: "27 Bancolombia Puerto Rico Internacional INC." },
  { id: 28, nombre: "28 Bancoomeva" },
  { id: 29, nombre: "29 Bank Of America National Association" },
  { id: 30, nombre: "30 BBVA Colombia" },
  { id: 31, nombre: "31 BCSC" },
  { id: 32, nombre: "32 BNP Paribas" },
  { id: 33, nombre: "33 Citibank" },
  { id: 34, nombre: "34 Citibank N.A." },
  { id: 35, nombre: "35 Colombian Santander Bank (Nassau) Limited" },
  { id: 36, nombre: "36 Colpatria Red Multibanca" },
  { id: 37, nombre: "37 Coopcentral" },
  { id: 38, nombre: "38 Corficolombiana" },
  { id: 39, nombre: "39 Deutsche Bank A.G." },
  { id: 40, nombre: "40 Finandina" },
  { id: 41, nombre: "41 Helm Bank" },
  { id: 42, nombre: "42 Helm Bank (Panamá) S.A." },
  { id: 43, nombre: "43 Helm Bank Cayman" },
  { id: 44, nombre: "44 Helm Bank USA" },
  { id: 45, nombre: "45 HSBC BANK (PANAMÁ) S.A." },
  { id: 46, nombre: "46 HSBC Bank USA N.A." },
  { id: 47, nombre: "47 HSBC Colombia" },
  { id: 48, nombre: "48 ITAÚ BBA Colombia S.A." },
  { id: 49, nombre: "49 JP Morgan" },
  { id: 50, nombre: "50 Multibank Inc." },
  { id: 51, nombre: "51 Procredit" },
  { id: 52, nombre: "52 The Bank Of New York Mellon" },
  { id: 53, nombre: "53 The Bank Of Nova Scotia (Toronto - Canadá)" },
  { id: 54, nombre: "54 The Royal Bank Of Canadá" },
  { id: 55, nombre: "55 Wells Fargo Bank, National Association" },
  { id: 56, nombre: "56 WWB" },
  { id: 57, nombre: "57 Otra entidad nacional" },
  { id: 58, nombre: "58 Otra entidad internacional" },
  { id: 59, nombre: "59 Sin cuenta - Efectivo" },
];

// Bancos a trabajar
const bancosFiltrados = bancos.filter(b =>
  [2, 24, 30, 36, 6, 57, 48, 15].includes(b.id)
);

// Ordenar por nombre alfabéticamente (sin modificar los ids)
bancosFiltrados.sort((a, b) => a.nombre.localeCompare(b.nombre, "es"));

export { bancos, bancosFiltrados };


export const tiposCaja = [
  { id: 1, nombre: "Caja Menor" },
  { id: 2, nombre: "Caja Principal" },
  { id: 3, nombre: "Cuenta Bancaria" },
];

export const tiposCuenta = [
  { id: 1, nombre: "1 Ahorros" },
  { id: 2, nombre: "2 Corriente" },
  { id: 3, nombre: "3 En efectivo" },
];

export const monedas = [
  { id: 1, nombre: "PESOS" },
  { id: 2, nombre: "DÓLAR" },
  { id: 3, nombre: "EURO" },
  { id: 4, nombre: "YEN" },
  { id: 5, nombre: "OTRA (Favor indicar cual en observaciones)" },
];

export const utilizaciones = [
  { id: "17447997354", nombre: "Caja Menor SGC", fecha: "2009/02/13" },
  { id: "3130199622", nombre: "Manejo de recursos propios para todos los pagos de la empresa", fecha: "2006/12/26" },
  { id: "12602165858", nombre: "Manejo Cto Interadmvo CO1.PCCNTR.2978784", fecha: "1999/04/06" },
  { id: "3184764040", nombre: "Manejo Convenio Interadmvo N° 124/FUGA 364/ERU DE 2018", fecha: "2017/11/09" },
  { id: "3100009224", nombre: "Manejo Conv Interad Derivado No. 02 del Conv Marco 932 de 2021 Derivados 1 y 3", fecha: "2024/12/23" },
  { id: "5500000246", nombre: "Manejo de recursos convenio IDEP N°273 /2025", fecha: "2025/05/05" },
  { id: "309037570", nombre: "Manejo Conv Interad Derivado No. 02 del Conv Marco 932 de 2021 Derivados 1 y 3", fecha: "2017/01/25" },
  { id: "144004835", nombre: "Caja Menor SGI", fecha: "2001/07/22" },
  { id: "144043080", nombre: "Manejo de recursos propios para todos los pagos de la empresa", fecha: "2001/02/14" },
  { id: "309055218", nombre: "Manejo Cto Interadmvo CO1.PCCNTR.4352924", fecha: "2022/12/28" },
  { id: "278832084", nombre: "Manejo de recursos propios para todos los pagos de la empresa", fecha: "2011/09/09" },
  { id: "278889233", nombre: "Manejo Convenio SDA 142 2024", fecha: "2011/09/09" },
  { id: "278889670", nombre: "Manejo recursoso propios", fecha: "2024/06/01" },
  { id: "4502008873", nombre: "Manejo Convenio 1210200-295-2014 de 2014", fecha: "2014/09/05" },
  { id: "4502009460", nombre: "Recaudos Brisas del Tintal", fecha: "2014/10/21" },
  { id: "622995025", nombre: "Actuación Estratégica Distrito Aeroportuario Engativá", fecha: "2024/08/28" },
  { id: "214114089", nombre: "Manejo Convenio1058 de 2009", fecha: "2009/10/20" },
  { id: "1221201000015", nombre: "Manejo de recursos propios para todos los pagos de la empresa", fecha: "2025/02/28" },
  { id: "1101201000521", nombre: "Manejo de recursos propios para todos los pagos de la empresa", fecha: "2025/03/25" },
];