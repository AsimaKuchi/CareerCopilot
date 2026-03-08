import { formatJobDescription } from "@/utils/formatJobDescription";

/**
 * FormattedJobDescription - Renders job descriptions with proper formatting
 * - Section headers are bold and styled
 * - Lists are rendered as bullet points
 * - Paragraphs have proper spacing
 */
export default function FormattedJobDescription({ description, className = "" }) {
  if (!description) {
    return (
      <p className="text-sm text-muted-foreground italic">
        No description available.
      </p>
    );
  }

  const elements = formatJobDescription(description);

  // Group consecutive bullets together
  const groupedElements = [];
  let currentBulletGroup = [];
  
  elements.forEach((el, idx) => {
    if (el.type === 'bullet') {
      currentBulletGroup.push(el);
    } else {
      if (currentBulletGroup.length > 0) {
        groupedElements.push({ type: 'bullet-group', items: currentBulletGroup, key: `bg-${idx}` });
        currentBulletGroup = [];
      }
      groupedElements.push(el);
    }
  });
  
  // Don't forget any remaining bullets
  if (currentBulletGroup.length > 0) {
    groupedElements.push({ type: 'bullet-group', items: currentBulletGroup, key: `bg-final` });
  }

  return (
    <div className={`space-y-3 ${className}`}>
      {groupedElements.map((el) => {
        switch (el.type) {
          case 'header':
            return (
              <h4 
                key={el.key} 
                className="text-sm font-semibold text-indigo-300 mt-4 first:mt-0 pb-1 border-b border-indigo-500/20"
              >
                {el.content}
              </h4>
            );
          case 'bullet-group':
            return (
              <ul key={el.key} className="space-y-1.5 pl-1">
                {el.items.map((item) => (
                  <li key={item.key} className="flex gap-2 text-sm text-muted-foreground">
                    <span className="text-indigo-400 flex-shrink-0 mt-1">•</span>
                    <span className="leading-relaxed">{item.content}</span>
                  </li>
                ))}
              </ul>
            );
          case 'bullet':
            return (
              <div key={el.key} className="flex gap-2 text-sm text-muted-foreground pl-1">
                <span className="text-indigo-400 flex-shrink-0 mt-0.5">•</span>
                <span className="leading-relaxed">{el.content}</span>
              </div>
            );
          default:
            return (
              <p key={el.key} className="text-sm text-muted-foreground leading-relaxed">
                {el.content}
              </p>
            );
        }
      })}
    </div>
  );
}
