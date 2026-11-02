import React from 'react'

export default function StatusOverview() {
  return (
    <section className="p-6 max-w-4xl mx-auto">
      <header className="mb-6">
        <h1 className="text-2xl font-bold">PetroLúmen</h1>
        <p className="text-sm text-gray-600">Plataforma Avançada de Engenharia de Petróleo</p>
      </header>

      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="rounded-lg shadow p-4 bg-white">
          <div className="text-sm text-gray-500">Sistema — Status dos Módulos</div>
          <div className="mt-2 text-3xl font-extrabold text-green-600">100%</div>
          <div className="mt-1 text-xs text-gray-600">Todos os módulos operacionais</div>
        </div>

        <div className="rounded-lg shadow p-4 bg-white">
          <div className="text-sm text-gray-500">Simulações — Status das Simulações</div>
          <div className="mt-2 text-3xl font-extrabold text-indigo-600">24</div>
          <div className="mt-1 text-xs text-gray-600">Simulações concluídas hoje</div>
        </div>

        <div className="rounded-lg shadow p-4 bg-white">
          <div className="text-sm text-gray-500">IA &amp; Analytics — Status dos Modelos</div>
          <div className="mt-2 text-3xl font-extrabold text-yellow-600">8</div>
          <div className="mt-1 text-xs text-gray-600">Modelos de IA ativos</div>
        </div>
      </div>
    </section>
  )
}
