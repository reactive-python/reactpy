import {
  createElementAttributes,
  createElementChildren,
} from "./element-utils.js";

export function loadModelImportSource(layoutContext, importSource) {
  return layoutContext
    .loadImportSource(importSource.source, importSource.sourceType)
    .then((module) => {
      if (typeof module.bind === "function") {
        return {
          data: importSource,
          bind: (node) => {
            const shortImportSource = {
              source: importSource.source,
              sourceType: importSource.sourceType,
            };
            const binding = module.bind(node, layoutContext);
            if (
              typeof binding.create === "function" &&
              typeof binding.render === "function" &&
              typeof binding.unmount === "function"
            ) {
              return {
                render: (model) =>
                  binding.render(
                    createElementFromModuleBinding(
                      layoutContext,
                      importSource,
                      module,
                      binding,
                      model
                    )
                  ),
                unmount: binding.unmount,
              };
            } else {
              console.error(
                `${importSource.source} returned an impropper binding`
              );
            }
          },
        };
      } else {
        console.error(
          `${importSource.source} did not export a function 'bind'`
        );
      }
    });
}

function createElementFromModuleBinding(
  layoutContext,
  currentImportSource,
  module,
  binding,
  model
) {
  let type;
  if (model.importSource) {
    if (!isImportSourceEqual(currentImportSource, model.importSource)) {
      console.error(
        "Parent element import source " +
          stringifyImportSource(currentImportSource) +
          " does not match child's import source " +
          stringifyImportSource(model.importSource)
      );
      return null;
    } else if (!module[model.tagName]) {
      console.error(
        "Module from source " +
          stringifyImportSource(currentImportSource) +
          ` does not export ${model.tagName}`
      );
      return null;
    } else {
      type = module[model.tagName];
    }
  } else {
    type = model.tagName;
  }
  return binding.create(
    type,
    createElementAttributes(model, layoutContext.sendEvent),
    createElementChildren(model, (child) =>
      createElementFromModuleBinding(
        layoutContext,
        currentImportSource,
        module,
        binding,
        child
      )
    )
  );
}

function isImportSourceEqual(source1, source2) {
  return (
    source1.source === source2.source &&
    source1.sourceType === source2.sourceType
  );
}

function stringifyImportSource(importSource) {
  return JSON.stringify({
    source: importSource.source,
    sourceType: importSource.sourceType,
  });
}
