import { Link } from 'react-router-dom'

const SECTIONS: { title: string; body: React.ReactNode }[] = [
  {
    title: '1. Quién es responsable de los datos',
    body: (
      <>
        Cada profesional que usa NutriApp es el <strong>responsable</strong> de los datos de sus pacientes: decide qué
        registra y para qué. NutriApp actúa como <strong>encargado del tratamiento</strong>: almacena y procesa esos
        datos solo para prestar el servicio y nunca los vende ni los usa con otros fines. Cada cuenta ve únicamente a
        sus propios pacientes.
      </>
    ),
  },
  {
    title: '2. Qué datos se tratan',
    body: (
      <ul className="list-disc pl-5 space-y-1">
        <li>Identificación y contacto del paciente (nombre, fecha de nacimiento, sexo, teléfono, correo, dirección).</li>
        <li>Datos de salud: antecedentes clínicos, alergias, evaluaciones antropométricas ISAK, pautas alimentarias y citas.</li>
        <li>Del profesional: nombre, correo, datos del consultorio y registros de acceso (fecha, acción, IP).</li>
      </ul>
    ),
  },
  {
    title: '3. Finalidad y base legal',
    body: (
      <>
        Los datos se usan para la atención nutricional del paciente: evaluación, seguimiento y entrega de pautas e
        informes. Los datos de salud son datos sensibles (Ley 19.628, modificada por la Ley 21.719), por lo que el
        profesional debe contar con el <strong>consentimiento expreso</strong> del paciente y registrarlo en su ficha
        («Registrar consentimiento»).
      </>
    ),
  },
  {
    title: '4. Conservación',
    body: (
      <>
        La ficha clínica se conserva por un mínimo de <strong>15 años</strong> desde la última atención, conforme a la
        normativa de fichas clínicas (Ley 20.584 y su reglamento). Cumplido el plazo, o antes si la ley lo permite y el
        paciente lo solicita, el profesional puede eliminar la ficha; la eliminación es definitiva y solo queda en las
        copias de respaldo hasta que éstas expiran.
      </>
    ),
  },
  {
    title: '5. Derechos del paciente',
    body: (
      <>
        El paciente puede pedir a su profesional acceder a sus datos, rectificarlos, oponerse a su tratamiento,
        solicitar su supresión o recibirlos en un formato portable. El profesional puede descargar la ficha completa
        con «Exportar ficha» y editar o eliminar los registros desde la aplicación.
      </>
    ),
  },
  {
    title: '6. Seguridad',
    body: (
      <ul className="list-disc pl-5 space-y-1">
        <li>Conexiones cifradas (HTTPS) y contraseñas guardadas con hash bcrypt.</li>
        <li>Verificación en dos pasos opcional para cada profesional.</li>
        <li>Registro de auditoría de accesos, exportaciones y cambios.</li>
        <li>Respaldos periódicos cifrados.</li>
      </ul>
    ),
  },
  {
    title: '7. Proveedores',
    body: (
      <>
        NutriApp usa proveedores de infraestructura para alojar la aplicación y la base de datos (Railway, Vercel) y
        para los respaldos (Cloudflare R2). Las funciones de inteligencia artificial (ideas de menú y sugerencias)
        envían a Anthropic solo datos clínicos necesarios — sexo, edad, peso, medidas y la pauta —, sin el nombre ni
        los datos de contacto del paciente.
      </>
    ),
  },
]

/** Política de privacidad y tratamiento de datos (pública). */
export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-bg-light py-10 px-4">
      <div className="max-w-3xl mx-auto bg-white rounded-xl shadow-sm border border-border p-8 space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Política de privacidad y tratamiento de datos</h1>
          <p className="text-sm text-text-muted mt-1">Versión 2026-10 · NutriApp</p>
        </div>
        {SECTIONS.map(s => (
          <section key={s.title} className="space-y-2">
            <h2 className="text-base font-semibold text-gray-900">{s.title}</h2>
            <div className="text-sm text-gray-700 leading-relaxed">{s.body}</div>
          </section>
        ))}
        <p className="text-xs text-text-muted border-t border-border pt-4">
          Este texto es una base de referencia; cada profesional debe revisarlo según su práctica.
        </p>
        <Link to="/login" className="inline-block text-sm text-primary font-medium hover:underline">← Volver</Link>
      </div>
    </div>
  )
}
