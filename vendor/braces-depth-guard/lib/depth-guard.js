'use strict';

// Security bounds are fixed: user options cannot increase or disable them.
const MAX_NESTING = 64;
const MAX_AST_VISITS = 131072;
const nestingError = () => new SyntaxError(`Brace AST nesting exceeds fixed limit (${MAX_NESTING})`);

/** Iterative depth-first validation follows only nodes, never parent or prev.
 * Parser ASTs have intentional reference cycles through parent/prev. A nodes
 * back-edge is a different, invalid cycle. Shared subtrees are allowed, but each
 * traversal is counted so a small exponentially shared DAG cannot bypass the
 * validation work bound. No recursive code runs before validation succeeds.
 */
const validateAst = ast => {
  const active = new Set();
  const stack = [{ node: ast, depth: 0, child: -1 }];
  let visits = 0;
  while (stack.length) {
    const frame = stack[stack.length - 1];
    const node = frame.node;
    if (frame.child === -1) {
      if (++visits > MAX_AST_VISITS) throw new SyntaxError('Brace AST exceeds fixed node traversal limit');
      if (!node || typeof node !== 'object' || Array.isArray(node)) throw new SyntaxError('Invalid brace AST node');
      if (active.has(node)) throw new SyntaxError('Cyclic brace AST nodes');
      if (node.nodes !== undefined && !Array.isArray(node.nodes)) throw new SyntaxError('Invalid brace AST nodes');
      if (node.value !== undefined && typeof node.value !== 'string') throw new SyntaxError('Invalid brace AST text');
      // Root is depth zero. Up to 64 containers and their terminal leaf are safe.
      if (frame.depth > MAX_NESTING && node.nodes !== undefined) throw nestingError();
      if (frame.depth > MAX_NESTING + 1) throw nestingError();
      active.add(node);
      frame.child = 0;
    }
    if (node.nodes && frame.child < node.nodes.length) {
      stack.push({ node: node.nodes[frame.child++], depth: frame.depth + 1, child: -1 });
    } else {
      active.delete(node);
      stack.pop();
    }
  }
};

module.exports = { MAX_NESTING, validateAst, nestingError };
