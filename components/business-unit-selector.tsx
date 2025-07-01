"use client";

import React from "react";
import { Card, CardContent } from "@/components/ui/card";

interface BusinessUnitSelectorProps {
  onSelect: (unit: "promoselect" | "suitup") => void;
}

export function BusinessUnitSelector({ onSelect }: BusinessUnitSelectorProps) {
  return (
    <Card className="w-full max-w-md mx-auto my-4 bg-gradient-to-br from-blue-50 to-indigo-50">
      <CardContent className="p-6">
        <div className="text-center mb-6">
          <h3 className="font-semibold text-xl mb-2 text-gray-800">
            Selecciona tu Unidad de Negocio
          </h3>
          <p className="text-sm text-gray-600">
            Elige el tipo de productos promocionales que necesitas
          </p>
        </div>

        <div className="space-y-4">
          <button
            onClick={() => onSelect("promoselect")}
            className="w-full group relative overflow-hidden bg-gradient-to-r from-emerald-500 to-emerald-600 hover:from-emerald-600 hover:to-emerald-700 text-white font-semibold py-4 px-6 rounded-lg shadow-lg transition-all duration-200 transform hover:scale-105 hover:shadow-xl"
          >
            <div className="relative z-10">
              <div className="text-lg font-bold mb-1">Promoselect</div>
              <div className="text-sm opacity-90">
                Productos promocionales individuales
              </div>
            </div>
            <div className="absolute inset-0 bg-gradient-to-r from-emerald-400 to-emerald-500 opacity-0 group-hover:opacity-100 transition-opacity duration-200"></div>
          </button>

          <button
            onClick={() => onSelect("suitup")}
            className="w-full group relative overflow-hidden bg-gradient-to-r from-indigo-500 to-indigo-600 hover:from-indigo-600 hover:to-indigo-700 text-white font-semibold py-4 px-6 rounded-lg shadow-lg transition-all duration-200 transform hover:scale-105 hover:shadow-xl"
          >
            <div className="relative z-10">
              <div className="text-lg font-bold mb-1">SuitUp</div>
              <div className="text-sm opacity-90">
                Kits de productos promocionales
              </div>
            </div>
            <div className="absolute inset-0 bg-gradient-to-r from-indigo-400 to-indigo-500 opacity-0 group-hover:opacity-100 transition-opacity duration-200"></div>
          </button>
        </div>

        <div className="mt-6 text-center">
          <div className="flex justify-center gap-6 text-xs text-gray-500">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-emerald-500 rounded-full"></div>
              <span>Productos Individuales</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-indigo-500 rounded-full"></div>
              <span>Kits Especializados</span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
} 