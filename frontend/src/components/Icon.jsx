import {
  FileText,
  Scale,
  ShieldAlert,
  Lightbulb,
  Search,
  Sparkles,
  Hammer,
  Send,
  Paperclip,
  MessageSquare,
  ChevronLeft,
  ChevronRight,
  Bot,
  User,
  Plus,
  Settings,
  History,
  X,
} from 'lucide-react';

const iconMap = {
  FileText,
  Scale,
  ShieldAlert,
  Lightbulb,
  Search,
  Sparkles,
  Hammer,
  Send,
  Paperclip,
  MessageSquare,
  ChevronLeft,
  ChevronRight,
  Bot,
  User,
  Plus,
  Settings,
  History,
  X,
};

export function Icon({ name, ...props }) {
  const Component = iconMap[name];
  if (!Component) return null;
  return <Component {...props} />;
}
