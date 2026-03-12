"""
🧠 BOF LEARNING SYSTEM
Analiza scripts de Carol y mejora el sistema automáticamente
"""

from typing import Dict, List, Tuple
import re
from collections import Counter
from config import BOF_CONFIG

class BOFLearningSystem:
    """Sistema de aprendizaje para mejorar generación de scripts BOF"""
    
    def __init__(self):
        self.palabras_urgencia = set(BOF_CONFIG['palabras_urgencia'])
        self.palabras_cta = set(BOF_CONFIG['palabras_cta'])
        self.estructura = BOF_CONFIG['estructura_esperada']
    
    def analyze_carol_scripts(self, scripts: List[str]) -> Dict:
        """
        Analiza los scripts de Carol para identificar patrones
        
        Args:
            scripts: Lista de scripts BOF de Carol
        
        Returns:
            Diccionario con análisis completo
        """
        if not scripts:
            return {}
        
        analysis = {
            'total_scripts': len(scripts),
            'palabras_urgencia_usadas': self._extract_urgency_words(scripts),
            'palabras_cta_usadas': self._extract_cta_phrases(scripts),
            'longitud_promedio': self._average_length(scripts),
            'estructura_comun': self._analyze_structure(scripts),
            'patrones_open_loop': self._analyze_open_loops(scripts),
            'patrones_close_loop': self._analyze_close_loops(scripts),
            'frases_exitosas': self._find_successful_phrases(scripts)
        }
        
        return analysis
    
    def _extract_urgency_words(self, scripts: List[str]) -> Dict[str, int]:
        """Extrae y cuenta palabras de urgencia usadas"""
        all_text = ' '.join(scripts).lower()
        
        word_counts = {}
        for word in self.palabras_urgencia:
            count = all_text.count(word.lower())
            if count > 0:
                word_counts[word] = count
        
        # Buscar también palabras nuevas de urgencia
        urgency_patterns = [
            r'(quedan? \w+)',  # "quedan pocas", "queda poco"
            r'(últim[oa]s? \w+)',  # "últimas horas", "último día"
            r'(sol[oa] \w+)',  # "solo hoy", "solo hasta"
            r'(antes de \w+)',  # "antes de que suba"
        ]
        
        for pattern in urgency_patterns:
            matches = re.findall(pattern, all_text)
            for match in matches:
                if match not in word_counts:
                    word_counts[match] = all_text.count(match)
        
        # Ordenar por frecuencia
        return dict(sorted(word_counts.items(), key=lambda x: x[1], reverse=True))
    
    def _extract_cta_phrases(self, scripts: List[str]) -> Dict[str, int]:
        """Extrae frases de CTA"""
        all_text = ' '.join(scripts).lower()
        
        cta_counts = {}
        for cta in self.palabras_cta:
            count = all_text.count(cta.lower())
            if count > 0:
                cta_counts[cta] = count
        
        # Buscar patrones de CTA
        cta_patterns = [
            r'(toca\s+(?:el|ese)\s+carrito[^.!?]*)',
            r'(no\s+esperes[^.!?]*)',
            r'(aprovecha[^.!?]*)',
        ]
        
        for pattern in cta_patterns:
            matches = re.findall(pattern, all_text)
            for match in matches:
                if match.strip() not in [c.lower() for c in cta_counts.keys()]:
                    cta_counts[match.strip()] = all_text.count(match)
        
        return dict(sorted(cta_counts.items(), key=lambda x: x[1], reverse=True))
    
    def _average_length(self, scripts: List[str]) -> Dict:
        """Calcula longitudes promedio"""
        word_counts = [len(script.split()) for script in scripts]
        char_counts = [len(script) for script in scripts]
        
        return {
            'palabras_promedio': round(sum(word_counts) / len(word_counts), 1),
            'caracteres_promedio': round(sum(char_counts) / len(char_counts), 1),
            'palabras_min': min(word_counts),
            'palabras_max': max(word_counts)
        }
    
    def _analyze_structure(self, scripts: List[str]) -> Dict:
        """Analiza la estructura de los scripts"""
        structures = []
        
        for script in scripts:
            structure = self._identify_structure(script)
            structures.append(structure)
        
        # Encontrar estructura más común
        structure_counter = Counter(tuple(s.items()) for s in structures)
        most_common = dict(structure_counter.most_common(1)[0][0]) if structure_counter else {}
        
        return {
            'estructura_mas_comun': most_common,
            'variaciones': len(set(tuple(s.items()) for s in structures))
        }
    
    def _identify_structure(self, script: str) -> Dict:
        """Identifica la estructura de un script individual"""
        script_lower = script.lower()
        
        structure = {
            'tiene_pregunta_inicial': script.strip().startswith('¿'),
            'tiene_transition': any(t in script_lower for t in ['para conseguirlo', 'para pillarlo', 'para hacerlo', 'don\'t believe me']),
            'tiene_cta_explicito': 'carrito' in script_lower,
            'tiene_why': any(w in script_lower for w in ['para desbloquear', 'para activar', 'para get']),
            'tiene_value': any(v in script_lower for v in ['esto hace', 'esto hará', 'así']),
            'tiene_close_loop': 'en lugar de' in script_lower or 'instead of' in script_lower,
            'tiene_urgencia_final': any(u in script_lower for u in ['solo hoy', 'se acaba', 'termina', 'última'])
        }
        
        return structure
    
    def _analyze_open_loops(self, scripts: List[str]) -> List[str]:
        """Analiza los hooks/open loops más usados"""
        open_loops = []
        
        for script in scripts:
            # Extraer primera oración
            first_sentence = script.split('.')[0] if '.' in script else script.split('?')[0] + '?'
            if first_sentence.strip():
                open_loops.append(first_sentence.strip())
        
        # Contar patrones
        counter = Counter(open_loops)
        return [hook for hook, count in counter.most_common(10)]
    
    def _analyze_close_loops(self, scripts: List[str]) -> List[str]:
        """Analiza los cierres más usados"""
        close_patterns = [
            r'(esto\s+har[áa]\s+que[^.!?]+[.!?])',
            r'(así[^.!?]+[.!?])',
            r'(en\s+lugar\s+de[^.!?]+[.!?])',
        ]
        
        closes = []
        for script in scripts:
            for pattern in close_patterns:
                matches = re.findall(pattern, script.lower())
                closes.extend(matches)
        
        counter = Counter(closes)
        return [close for close, count in counter.most_common(5)]
    
    def _find_successful_phrases(self, scripts: List[str]) -> List[str]:
        """Encuentra frases que aparecen frecuentemente (probablemente exitosas)"""
        # Extraer frases de 3-6 palabras
        all_phrases = []
        
        for script in scripts:
            words = script.lower().split()
            for n in range(3, 7):  # 3-6 palabras
                for i in range(len(words) - n + 1):
                    phrase = ' '.join(words[i:i+n])
                    all_phrases.append(phrase)
        
        # Contar y filtrar
        counter = Counter(all_phrases)
        # Solo frases que aparecen 2+ veces
        successful = [phrase for phrase, count in counter.most_common(20) if count >= 2]
        
        return successful
    
    def compare_with_system(self, carol_analysis: Dict, system_scripts: List[str]) -> Dict:
        """
        Compara scripts de Carol con los que genera el sistema
        
        Args:
            carol_analysis: Análisis de scripts de Carol
            system_scripts: Scripts generados por el sistema (si los hay)
        
        Returns:
            Diccionario con comparación y recomendaciones
        """
        if not system_scripts:
            return {
                'mensaje': 'No hay scripts del sistema aún para comparar',
                'recomendaciones': self._generate_initial_recommendations(carol_analysis)
            }
        
        system_analysis = self.analyze_carol_scripts(system_scripts)
        
        comparison = {
            'urgencia': self._compare_urgency(
                carol_analysis['palabras_urgencia_usadas'],
                system_analysis['palabras_urgencia_usadas']
            ),
            'cta': self._compare_cta(
                carol_analysis['palabras_cta_usadas'],
                system_analysis['palabras_cta_usadas']
            ),
            'longitud': self._compare_length(
                carol_analysis['longitud_promedio'],
                system_analysis['longitud_promedio']
            ),
            'similitud_score': self._calculate_similarity(carol_analysis, system_analysis)
        }
        
        comparison['recomendaciones'] = self._generate_recommendations(comparison)
        
        return comparison
    
    def _compare_urgency(self, carol_words: Dict, system_words: Dict) -> Dict:
        """Compara uso de palabras de urgencia"""
        carol_total = sum(carol_words.values())
        system_total = sum(system_words.values()) if system_words else 0
        
        missing_words = [word for word in carol_words if word not in system_words]
        overused_words = [word for word in system_words if word not in carol_words]
        
        return {
            'carol_total': carol_total,
            'system_total': system_total,
            'diferencia': abs(carol_total - system_total),
            'palabras_que_faltan': missing_words[:5],
            'palabras_de_mas': overused_words[:5],
            'top_carol': list(carol_words.keys())[:5]
        }
    
    def _compare_cta(self, carol_ctas: Dict, system_ctas: Dict) -> Dict:
        """Compara uso de CTAs"""
        return {
            'carol_variedad': len(carol_ctas),
            'system_variedad': len(system_ctas) if system_ctas else 0,
            'ctas_carol': list(carol_ctas.keys())[:5],
            'ctas_system': list(system_ctas.keys())[:5] if system_ctas else []
        }
    
    def _compare_length(self, carol_length: Dict, system_length: Dict) -> Dict:
        """Compara longitudes"""
        if not system_length:
            return {'mensaje': 'No hay datos del sistema'}
        
        return {
            'carol_promedio': carol_length['palabras_promedio'],
            'system_promedio': system_length['palabras_promedio'],
            'diferencia': abs(carol_length['palabras_promedio'] - system_length['palabras_promedio']),
            'recomendacion': 'más corto' if carol_length['palabras_promedio'] < system_length['palabras_promedio'] else 'más largo'
        }
    
    def _calculate_similarity(self, carol_analysis: Dict, system_analysis: Dict) -> int:
        """Calcula score de similitud 0-100"""
        score = 0
        
        # Longitud similar (25 puntos)
        length_diff = abs(
            carol_analysis['longitud_promedio']['palabras_promedio'] - 
            system_analysis['longitud_promedio']['palabras_promedio']
        )
        score += max(0, 25 - length_diff)
        
        # Palabras urgencia (35 puntos)
        carol_urgency = set(carol_analysis['palabras_urgencia_usadas'].keys())
        system_urgency = set(system_analysis['palabras_urgencia_usadas'].keys())
        urgency_overlap = len(carol_urgency & system_urgency) / max(len(carol_urgency), 1)
        score += int(urgency_overlap * 35)
        
        # CTAs (20 puntos)
        carol_ctas = set(carol_analysis['palabras_cta_usadas'].keys())
        system_ctas = set(system_analysis['palabras_cta_usadas'].keys())
        cta_overlap = len(carol_ctas & system_ctas) / max(len(carol_ctas), 1)
        score += int(cta_overlap * 20)
        
        # Estructura (20 puntos)
        carol_struct = carol_analysis['estructura_comun']['estructura_mas_comun']
        system_struct = system_analysis['estructura_comun']['estructura_mas_comun']
        struct_match = sum(1 for k in carol_struct if carol_struct.get(k) == system_struct.get(k))
        score += int((struct_match / max(len(carol_struct), 1)) * 20)
        
        return min(100, max(0, score))
    
    def _generate_initial_recommendations(self, carol_analysis: Dict) -> List[str]:
        """Genera recomendaciones iniciales basadas solo en Carol"""
        recs = []
        
        # Palabras de urgencia top
        top_urgency = list(carol_analysis['palabras_urgencia_usadas'].keys())[:3]
        recs.append(f"Usar más estas palabras de urgencia: {', '.join(top_urgency)}")
        
        # CTAs top
        top_ctas = list(carol_analysis['palabras_cta_usadas'].keys())[:3]
        recs.append(f"CTAs más efectivos de Carol: {', '.join(top_ctas)}")
        
        # Longitud
        avg_words = carol_analysis['longitud_promedio']['palabras_promedio']
        recs.append(f"Mantener longitud around {int(avg_words)} palabras")
        
        # Open loops
        if carol_analysis['patrones_open_loop']:
            recs.append(f"Hooks exitosos: {carol_analysis['patrones_open_loop'][0]}")
        
        return recs
    
    def _generate_recommendations(self, comparison: Dict) -> List[str]:
        """Genera recomendaciones de mejora"""
        recs = []
        
        # Urgencia
        if comparison['urgencia']['palabras_que_faltan']:
            missing = ', '.join(comparison['urgencia']['palabras_que_faltan'][:3])
            recs.append(f"❗ Añadir palabras de urgencia: {missing}")
        
        # CTAs
        if comparison['cta']['carol_variedad'] > comparison['cta']['system_variedad']:
            recs.append(f"❗ Aumentar variedad de CTAs (Carol usa {comparison['cta']['carol_variedad']}, sistema solo {comparison['cta']['system_variedad']})")
        
        # Longitud
        if comparison['longitud'].get('diferencia', 0) > 10:
            recs.append(f"❗ Ajustar longitud: hacer scripts {comparison['longitud']['recomendacion']}")
        
        # Score general
        if comparison['similitud_score'] < 70:
            recs.append(f"⚠️ Similitud baja ({comparison['similitud_score']}%) - revisar estructura general")
        elif comparison['similitud_score'] >= 85:
            recs.append(f"✅ Excelente similitud ({comparison['similitud_score']}%) - mantener approach")
        
        return recs if recs else ["✅ Sistema bien calibrado con estilo de Carol"]
    
    def generate_report(self, carol_scripts: List[str], system_scripts: List[str] = None) -> str:
        """Genera reporte completo de análisis"""
        carol_analysis = self.analyze_carol_scripts(carol_scripts)
        comparison = self.compare_with_system(carol_analysis, system_scripts or [])
        
        report = f"""
╔══════════════════════════════════════════════════════════════╗
║           📊 REPORTE ANÁLISIS BOF LEARNING                   ║
╚══════════════════════════════════════════════════════════════╝

📈 ANÁLISIS SCRIPTS CAROL:
  • Total scripts analizados: {carol_analysis['total_scripts']}
  • Longitud promedio: {carol_analysis['longitud_promedio']['palabras_promedio']} palabras
  • Rango: {carol_analysis['longitud_promedio']['palabras_min']}-{carol_analysis['longitud_promedio']['palabras_max']} palabras

🔥 TOP PALABRAS URGENCIA:
"""
        for word, count in list(carol_analysis['palabras_urgencia_usadas'].items())[:5]:
            report += f"  • '{word}': {count} usos\n"
        
        report += "\n📢 TOP CTAs:\n"
        for cta, count in list(carol_analysis['palabras_cta_usadas'].items())[:5]:
            report += f"  • '{cta}': {count} usos\n"
        
        report += f"\n🎣 HOOKS MÁS USADOS:\n"
        for hook in carol_analysis['patrones_open_loop'][:3]:
            report += f"  • {hook}\n"
        
        if system_scripts:
            report += f"\n\n🔄 COMPARACIÓN CON SISTEMA:\n"
            report += f"  • Score similitud: {comparison['similitud_score']}%\n"
            report += f"\n💡 RECOMENDACIONES:\n"
            for rec in comparison['recomendaciones']:
                report += f"  {rec}\n"
        else:
            report += f"\n\n💡 RECOMENDACIONES INICIALES:\n"
            for rec in comparison['recomendaciones']:
                report += f"  • {rec}\n"
        
        report += "\n" + "═" * 64 + "\n"
        
        return report


# Testing
def test_learning_system():
    """Prueba el sistema de aprendizaje"""
    system = BOFLearningSystem()
    
    # Scripts de ejemplo (de Carol)
    carol_scripts = [
        "¿1 batería magnética gratis? Para conseguirlo, solo... Toca el carrito naranja. Para desbloquear la oferta flash. Solo hoy - toca el carrito ya.",
        "3 baterías por menos de 24€. Para hacerlo, solo... Toca el carrito naranja. Quedan pocas unidades. No esperes - toca el carrito ahora.",
        "Última oportunidad - batería MagSafe. Para pillarlo... Toca ese carrito. Se acaba esta noche. Aprovecha antes de que suba."
    ]
    
    print(system.generate_report(carol_scripts))


if __name__ == "__main__":
    test_learning_system()
