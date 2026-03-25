// ============================================================
// ZENDA — Firebase Configuration & Database Helpers
// ============================================================
// INSTRUCCIONES:
// 1. Ve a console.firebase.google.com
// 2. Configuración ⚙️ → Tus apps → </>
// 3. Reemplaza el firebaseConfig de abajo con el tuyo
// ============================================================

import { initializeApp } from "https://www.gstatic.com/firebasejs/10.12.0/firebase-app.js";
import {
  getFirestore, collection, doc, setDoc, getDoc,
  getDocs, addDoc, updateDoc, deleteDoc,
  onSnapshot, serverTimestamp
} from "https://www.gstatic.com/firebasejs/10.12.0/firebase-firestore.js";
import {
  getAuth, signInWithEmailAndPassword,
  createUserWithEmailAndPassword, signOut, onAuthStateChanged
} from "https://www.gstatic.com/firebasejs/10.12.0/firebase-auth.js";

// ⚠️ REEMPLAZA CON TUS CLAVES DE FIREBASE
const firebaseConfig = {
  apiKey:            "TU_API_KEY",
  authDomain:        "TU_PROJECT.firebaseapp.com",
  projectId:         "TU_PROJECT_ID",
  storageBucket:     "TU_PROJECT.appspot.com",
  messagingSenderId: "TU_SENDER_ID",
  appId:             "TU_APP_ID"
};

const app  = initializeApp(firebaseConfig);
const db   = getFirestore(app);
const auth = getAuth(app);

// ── NEGOCIOS ──────────────────────────────────────────────
export async function crearNegocio(datos) {
  const ref = doc(collection(db, 'negocios'));
  await setDoc(ref, { ...datos, activo: true, plan: 'basico', creadoEn: serverTimestamp() });
  return ref.id;
}
export async function obtenerNegocio(id) {
  const s = await getDoc(doc(db, 'negocios', id));
  return s.exists() ? { id: s.id, ...s.data() } : null;
}
export async function obtenerTodosNegocios() {
  const s = await getDocs(collection(db, 'negocios'));
  return s.docs.map(d => ({ id: d.id, ...d.data() }));
}
export async function actualizarNegocio(id, datos) {
  await updateDoc(doc(db, 'negocios', id), datos);
}
export async function eliminarNegocio(id) {
  await updateDoc(doc(db, 'negocios', id), { activo: false });
}

// ── CITAS ─────────────────────────────────────────────────
export async function crearCita(negocioId, datos) {
  const r = await addDoc(collection(db, 'negocios', negocioId, 'citas'), {
    ...datos, creadoEn: serverTimestamp()
  });
  return r.id;
}
export async function obtenerCitas(negocioId) {
  const s = await getDocs(collection(db, 'negocios', negocioId, 'citas'));
  return s.docs.map(d => ({ id: d.id, ...d.data() }));
}
export function escucharCitas(negocioId, cb) {
  return onSnapshot(collection(db, 'negocios', negocioId, 'citas'),
    s => cb(s.docs.map(d => ({ id: d.id, ...d.data() }))));
}
export async function actualizarCita(negocioId, citaId, datos) {
  await updateDoc(doc(db, 'negocios', negocioId, 'citas', citaId), datos);
}
export async function eliminarCita(negocioId, citaId) {
  await deleteDoc(doc(db, 'negocios', negocioId, 'citas', citaId));
}

// ── PERSONAL ──────────────────────────────────────────────
export async function obtenerPersonal(negocioId) {
  const s = await getDocs(collection(db, 'negocios', negocioId, 'personal'));
  return s.docs.map(d => ({ id: d.id, ...d.data() }));
}
export async function crearPersonal(negocioId, datos) {
  const r = await addDoc(collection(db, 'negocios', negocioId, 'personal'),
    { ...datos, creadoEn: serverTimestamp() });
  return r.id;
}
export async function actualizarPersonal(negocioId, staffId, datos) {
  await updateDoc(doc(db, 'negocios', negocioId, 'personal', staffId), datos);
}
export async function eliminarPersonal(negocioId, staffId) {
  await deleteDoc(doc(db, 'negocios', negocioId, 'personal', staffId));
}

// ── HORARIOS ──────────────────────────────────────────────
export async function obtenerHorarios(negocioId) {
  const s = await getDocs(collection(db, 'negocios', negocioId, 'horarios'));
  return s.docs.map(d => ({ id: d.id, ...d.data() }));
}
export async function guardarHorarios(negocioId, horarios) {
  await Promise.all(horarios.map((h, i) =>
    setDoc(doc(db, 'negocios', negocioId, 'horarios', String(i)), h)));
}

// ── SERVICIOS ─────────────────────────────────────────────
export async function obtenerServicios(negocioId) {
  const s = await getDocs(collection(db, 'negocios', negocioId, 'servicios'));
  return s.docs.map(d => ({ id: d.id, ...d.data() }));
}
export async function crearServicio(negocioId, datos) {
  const r = await addDoc(collection(db, 'negocios', negocioId, 'servicios'), datos);
  return r.id;
}
export async function eliminarServicio(negocioId, svcId) {
  await deleteDoc(doc(db, 'negocios', negocioId, 'servicios', svcId));
}

// ── AUTH ──────────────────────────────────────────────────
export const loginEmail    = (e, p) => signInWithEmailAndPassword(auth, e, p);
export const registrar     = (e, p) => createUserWithEmailAndPassword(auth, e, p);
export const cerrarSesion  = ()     => signOut(auth);
export const onAuth        = (cb)   => onAuthStateChanged(auth, cb);
export async function obtenerUsuario(uid) {
  const s = await getDoc(doc(db, 'usuarios', uid));
  return s.exists() ? { id: s.id, ...s.data() } : null;
}
export async function crearUsuarioDoc(uid, datos) {
  await setDoc(doc(db, 'usuarios', uid), datos);
}

export { db, auth };
