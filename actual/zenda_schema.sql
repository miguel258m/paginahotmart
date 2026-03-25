-- ============================================================
-- ZENDA — Schema completo
-- Ejecutar en Supabase → SQL Editor → New query
-- ============================================================

-- 1. NEGOCIOS (businesses)
-- Cada negocio que se registra en Zenda
CREATE TABLE negocios (
  id            UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  nombre        TEXT NOT NULL,
  tipo          TEXT NOT NULL, -- 'barberia' | 'clinica' | 'spa' | 'salon' | 'doctor'
  url_slug      TEXT UNIQUE NOT NULL, -- ej: 'clinica-vida'
  email         TEXT UNIQUE NOT NULL,
  whatsapp      TEXT,
  direccion     TEXT,
  descripcion   TEXT,
  logo_url      TEXT,
  plan          TEXT DEFAULT 'trial', -- 'trial' | 'basic' | 'pro' | 'business'
  estado        TEXT DEFAULT 'pendiente', -- 'pendiente' | 'activo' | 'rechazado' | 'inactivo'
  motivo_rechazo TEXT,
  created_at    TIMESTAMPTZ DEFAULT NOW(),
  updated_at    TIMESTAMPTZ DEFAULT NOW()
);

-- 2. USUARIOS (auth + roles)
-- Vinculado a auth.users de Supabase
CREATE TABLE usuarios (
  id            UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  auth_id       UUID UNIQUE REFERENCES auth.users(id) ON DELETE CASCADE,
  negocio_id    UUID REFERENCES negocios(id) ON DELETE CASCADE,
  nombre        TEXT NOT NULL,
  email         TEXT NOT NULL,
  rol           TEXT NOT NULL DEFAULT 'admin', -- 'superadmin' | 'admin' | 'medico' | 'recepcion'
  activo        BOOLEAN DEFAULT true,
  created_at    TIMESTAMPTZ DEFAULT NOW()
);

-- 3. PERSONAL (staff por negocio)
CREATE TABLE personal (
  id            UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  negocio_id    UUID NOT NULL REFERENCES negocios(id) ON DELETE CASCADE,
  usuario_id    UUID REFERENCES usuarios(id),
  nombre        TEXT NOT NULL,
  especialidad  TEXT,
  experiencia_anos INT DEFAULT 0,
  email         TEXT,
  whatsapp      TEXT,
  precio_consulta NUMERIC(10,2) DEFAULT 0,
  duracion_min  INT DEFAULT 30,
  activo        BOOLEAN DEFAULT true,
  dias_disponibles TEXT[] DEFAULT ARRAY['lunes','martes','miercoles','jueves','viernes'],
  hora_inicio   TIME DEFAULT '08:00',
  hora_fin      TIME DEFAULT '18:00',
  created_at    TIMESTAMPTZ DEFAULT NOW()
);

-- 4. SERVICIOS
CREATE TABLE servicios (
  id            UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  negocio_id    UUID NOT NULL REFERENCES negocios(id) ON DELETE CASCADE,
  personal_id   UUID REFERENCES personal(id),
  nombre        TEXT NOT NULL,
  descripcion   TEXT,
  categoria     TEXT,
  precio        NUMERIC(10,2) NOT NULL,
  duracion_min  INT DEFAULT 30,
  activo        BOOLEAN DEFAULT true,
  visible_booking BOOLEAN DEFAULT true,
  created_at    TIMESTAMPTZ DEFAULT NOW()
);

-- 5. CITAS
CREATE TABLE citas (
  id            UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  negocio_id    UUID NOT NULL REFERENCES negocios(id) ON DELETE CASCADE,
  personal_id   UUID REFERENCES personal(id),
  servicio_id   UUID REFERENCES servicios(id),
  -- Datos del paciente/cliente
  paciente_nombre TEXT NOT NULL,
  paciente_dni    TEXT,
  paciente_email  TEXT,
  paciente_phone  TEXT,
  paciente_fecha_nacimiento DATE,
  -- Cita
  fecha         DATE NOT NULL,
  hora          TIME NOT NULL,
  motivo        TEXT,
  notas         TEXT,
  precio        NUMERIC(10,2),
  -- Estado
  estado        TEXT DEFAULT 'pendiente', -- 'pendiente' | 'confirmada' | 'cancelada' | 'completada'
  motivo_cancelacion TEXT,
  -- Ticket
  ticket_numero TEXT UNIQUE,
  -- Comprobante pago
  comprobante_url TEXT,
  comprobante_enviado_at TIMESTAMPTZ,
  -- Timestamps
  created_at    TIMESTAMPTZ DEFAULT NOW(),
  updated_at    TIMESTAMPTZ DEFAULT NOW()
);

-- 6. AVISOS (del superadmin a negocios)
CREATE TABLE avisos (
  id            UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  titulo        TEXT NOT NULL,
  mensaje       TEXT NOT NULL,
  tipo          TEXT DEFAULT 'notificacion', -- 'notificacion' | 'aviso' | 'actualizacion' | 'mantenimiento'
  para          TEXT DEFAULT 'todos', -- 'todos' | UUID de negocio específico
  leido_por     UUID[] DEFAULT ARRAY[]::UUID[], -- array de negocio_ids que lo leyeron
  created_at    TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- FUNCIONES Y TRIGGERS
-- ============================================================

-- Auto-generar ticket número al crear cita
CREATE OR REPLACE FUNCTION generar_ticket()
RETURNS TRIGGER AS $$
DECLARE
  prefijo TEXT;
  numero  TEXT;
BEGIN
  -- Prefijo según tipo de negocio
  SELECT 
    CASE tipo
      WHEN 'clinica' THEN 'CLV'
      WHEN 'barberia' THEN 'BBR'
      WHEN 'spa'      THEN 'SPA'
      WHEN 'salon'    THEN 'SAL'
      WHEN 'doctor'   THEN 'DOC'
      ELSE 'ZND'
    END INTO prefijo
  FROM negocios WHERE id = NEW.negocio_id;

  numero := prefijo || '-' || LPAD(FLOOR(RANDOM() * 9000 + 1000)::TEXT, 4, '0');
  
  -- Asegurar que sea único
  WHILE EXISTS (SELECT 1 FROM citas WHERE ticket_numero = numero) LOOP
    numero := prefijo || '-' || LPAD(FLOOR(RANDOM() * 9000 + 1000)::TEXT, 4, '0');
  END LOOP;
  
  NEW.ticket_numero := numero;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_generar_ticket
  BEFORE INSERT ON citas
  FOR EACH ROW
  WHEN (NEW.ticket_numero IS NULL)
  EXECUTE FUNCTION generar_ticket();

-- Auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_updated_at_citas
  BEFORE UPDATE ON citas
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

CREATE TRIGGER trigger_updated_at_negocios
  BEFORE UPDATE ON negocios
  FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- ============================================================
-- ROW LEVEL SECURITY (RLS)
-- ============================================================

ALTER TABLE negocios  ENABLE ROW LEVEL SECURITY;
ALTER TABLE usuarios  ENABLE ROW LEVEL SECURITY;
ALTER TABLE personal  ENABLE ROW LEVEL SECURITY;
ALTER TABLE servicios ENABLE ROW LEVEL SECURITY;
ALTER TABLE citas     ENABLE ROW LEVEL SECURITY;
ALTER TABLE avisos    ENABLE ROW LEVEL SECURITY;

-- Negocios: cualquiera puede registrarse (INSERT), solo el dueño puede ver/editar el suyo
CREATE POLICY "registro_publico" ON negocios FOR INSERT WITH CHECK (true);
CREATE POLICY "ver_propio_negocio" ON negocios FOR SELECT USING (
  id IN (SELECT negocio_id FROM usuarios WHERE auth_id = auth.uid())
);
CREATE POLICY "editar_propio_negocio" ON negocios FOR UPDATE USING (
  id IN (SELECT negocio_id FROM usuarios WHERE auth_id = auth.uid())
);

-- Personal: solo admins del negocio
CREATE POLICY "ver_personal_propio" ON personal FOR SELECT USING (
  negocio_id IN (SELECT negocio_id FROM usuarios WHERE auth_id = auth.uid())
);
CREATE POLICY "gestionar_personal" ON personal FOR ALL USING (
  negocio_id IN (SELECT negocio_id FROM usuarios WHERE auth_id = auth.uid() AND rol IN ('admin','superadmin'))
);

-- Servicios: solo del propio negocio, SELECT público para booking
CREATE POLICY "ver_servicios_publico" ON servicios FOR SELECT USING (visible_booking = true OR
  negocio_id IN (SELECT negocio_id FROM usuarios WHERE auth_id = auth.uid())
);
CREATE POLICY "gestionar_servicios" ON servicios FOR ALL USING (
  negocio_id IN (SELECT negocio_id FROM usuarios WHERE auth_id = auth.uid() AND rol IN ('admin','superadmin'))
);

-- Citas: booking público puede insertar, admins y médicos ven las suyas
CREATE POLICY "booking_publico" ON citas FOR INSERT WITH CHECK (true);
CREATE POLICY "ver_citas_negocio" ON citas FOR SELECT USING (
  negocio_id IN (SELECT negocio_id FROM usuarios WHERE auth_id = auth.uid())
);
CREATE POLICY "actualizar_citas" ON citas FOR UPDATE USING (
  negocio_id IN (SELECT negocio_id FROM usuarios WHERE auth_id = auth.uid())
);

-- Avisos: todos los autenticados los ven
CREATE POLICY "ver_avisos" ON avisos FOR SELECT USING (
  para = 'todos' OR 
  para IN (SELECT negocio_id::TEXT FROM usuarios WHERE auth_id = auth.uid())
);

-- ============================================================
-- DATOS INICIALES — Superadmin
-- ============================================================
-- IMPORTANTE: Después de crear tu usuario en Supabase Auth,
-- reemplaza 'TU-AUTH-UUID' con tu UUID real de auth.users

-- INSERT INTO usuarios (auth_id, nombre, email, rol, negocio_id)
-- VALUES ('TU-AUTH-UUID', 'Super Admin', 'tu@email.com', 'superadmin', NULL);

-- ============================================================
-- NEGOCIO DE PRUEBA — Clínica Vida
-- ============================================================
INSERT INTO negocios (nombre, tipo, url_slug, email, whatsapp, direccion, plan, estado)
VALUES ('Clínica Vida', 'clinica', 'clinica-vida', 'admin@clinicavida.com', '+52555000001', 'Av. Salud 420, Piso 3', 'pro', 'activo');
