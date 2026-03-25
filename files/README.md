# 🟣 Zenda — Sistema de Gestión de Citas

## Estructura del proyecto

```
zenda/
├── index.html        → Landing page (TikTok / captación)
├── login.html        → Login superadmin + negocios
├── superadmin.html   → Panel de TI (creas y gestionas clientes)
├── dashboard.html    → Panel del negocio (gestiona citas, personal, horarios)
├── reservar.html     → Página pública de reservas para pacientes
├── firebase.js       → Configuración y helpers de Firebase
└── README.md         → Este archivo
```

---

## 🔥 Paso 1 — Configurar Firebase

1. Ve a **console.firebase.google.com**
2. Crea un proyecto llamado `zenda`
3. Activa **Firestore Database** en modo de prueba
4. Activa **Authentication** → Email/contraseña
5. Ve a ⚙️ Configuración → Tus apps → `</>` → Registra `zenda-web`
6. Copia el `firebaseConfig` y pégalo en **firebase.js** reemplazando los valores

---

## 👤 Paso 2 — Crear tu cuenta de superadmin

En Firebase Console → Authentication → Agregar usuario:
- Email: `tu@email.com`
- Password: `tupassword`

Luego en Firestore → Colección `usuarios` → Documento con tu UID:
```json
{
  "email": "tu@email.com",
  "rol": "superadmin",
  "nombre": "Tu nombre"
}
```

---

## 🚀 Paso 3 — Subir a Vercel (gratis, sin dormir)

1. Crea cuenta en **vercel.com**
2. Instala Vercel CLI: `npm install -g vercel`
3. Entra a la carpeta del proyecto: `cd zenda`
4. Ejecuta: `vercel`
5. Sigue las instrucciones (proyecto nuevo, directorio raíz)
6. Tu app queda en: `https://zenda.vercel.app`

---

## 🔗 Subir a GitHub

```bash
git init
git add .
git commit -m "Zenda v1.0"
git branch -M main
git remote add origin https://github.com/TUUSUARIO/zenda.git
git push -u origin main
```

---

## 💡 Flujo de uso

```
1. Tú (superadmin) → login.html → superadmin.html
2. Creas un negocio → se genera un ID único
3. El negocio → login.html → dashboard.html?negocio=ID
4. El negocio comparte su link de reservas → reservar.html?negocio=ID
5. Paciente agenda → aparece en solicitudes del dashboard
6. El negocio confirma → cita confirmada en tiempo real
```

---

## 💜 Pago Yape

El link de WhatsApp se genera automáticamente al confirmar una cita.
Configura el número Yape de cada negocio en:
- `superadmin.html` → campo "Número Yape" al crear negocio
- `dashboard.html` → tab Configuración

---

## 📞 Soporte

Desarrollado con Zenda. Para actualizaciones o cambios, contacta al desarrollador.
