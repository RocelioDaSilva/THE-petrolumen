// Função utilitária para classes condicionais (usada em Card, Badge, etc)
export function cn(...classes: (string | undefined | false)[]) {
  return classes.filter(Boolean).join(' ');
}
